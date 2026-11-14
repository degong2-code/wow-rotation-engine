"""No-network tests for Korean spell-name evidence and publication safety."""
import io
import json
from urllib.error import HTTPError
import unittest

from engine.spell_names import (
    audit, fetch_snapshot, fetch_spell, fetch_spell_media, parse_spell_ids, inventory, oauth_token,
    SNAPSHOT_VERSION, SOURCE, LOCALE,
)


def snapshot(rows):
    return {
        "schema_version": SNAPSHOT_VERSION,
        "source": SOURCE,
        "region": "kr",
        "locale": LOCALE,
        "namespace": "static-kr",
        "checked_at_utc": "2026-11-10T09:00:00+00:00",
        "observations": rows,
    }


class NameEvidenceTests(unittest.TestCase):
    def test_baseline_inventory_has_176_spell_ids(self):
        names=inventory()
        self.assertEqual(len(names),176)
        self.assertEqual(names[133],["화염구"])

    def test_no_snapshot_is_never_verified(self):
        result=audit()
        self.assertFalse(result["publish_ready"])
        self.assertEqual(result["counts"]["distinct_spell_ids"],176)
        self.assertEqual(result["counts"]["inherited_name_records"],178)
        self.assertEqual(result["counts"]["not_checked"],176)
        self.assertEqual(result["counts"]["official_names_auto_approved"],0)

    def test_matching_and_missing_names_remain_pending(self):
        result=audit(snapshot=snapshot([
            {"spell_id":133,"status":"found","name_ko":"화염구"},
            {"spell_id":190319,"status":"not_found"},
        ]))
        self.assertEqual(result["counts"]["observations_found_matching"],1)
        self.assertEqual(result["counts"]["observations_not_found"],1)
        self.assertEqual(result["counts"]["not_checked"],174)
        self.assertFalse(result["publish_ready"])
        self.assertEqual(next(r for r in result["records"] if r["spell_id"]==133)["review"],"pending")

    def test_mismatched_name_is_not_corrected_automatically(self):
        result=audit(snapshot=snapshot([
            {"spell_id":133,"status":"found","name_ko":"임의의 변경 이름"}
        ]))
        record=next(r for r in result["records"] if r["spell_id"]==133)
        self.assertEqual(record["comparison"],"name_disagrees_with_inherited")
        self.assertEqual(record["inherited_names_ko"],["화염구"])
        self.assertEqual(record["review"],"pending")

    def test_duplicate_snapshot_ids_rejected(self):
        bad=snapshot([{"spell_id":133,"status":"not_found"}]*2)
        with self.assertRaises(ValueError):
            audit(snapshot=bad)

    def test_unknown_snapshot_id_rejected(self):
        with self.assertRaises(ValueError):
            audit(snapshot=snapshot([{"spell_id":987654321,"status":"not_found"}]))

    def test_wrong_locale_rejected(self):
        bad=snapshot([])
        bad["locale"]="en_US"
        with self.assertRaises(ValueError):
            audit(snapshot=bad)

    def test_invalid_found_name_rejected(self):
        with self.assertRaises(ValueError):
            audit(snapshot=snapshot([{"spell_id":133,"status":"found","name_ko":""}]))

    def test_error_observation_not_mistaken_for_mismatch(self):
        result=audit(snapshot=snapshot([{"spell_id":133,"status":"request_error","http_status":500}]))
        self.assertEqual(result["counts"]["observations_other_issue"],1)
        self.assertEqual(result["counts"]["observations_found_mismatching"],0)

    def test_oauth_token_uses_client_credentials(self):
        seen=[]
        def opener(request,timeout):
            seen.append(request)
            return io.BytesIO(b'{"access_token":"fake-token"}')
        token=oauth_token("example_id","example_secret",opener=opener)
        self.assertEqual(token,"fake-token")
        self.assertTrue(seen[0].full_url.endswith("/token"))
        self.assertEqual(seen[0].get_method(),"POST")
        self.assertIn("Basic ",seen[0].get_header("Authorization"))

    def test_spell_response_requires_same_id(self):
        def opener(request,timeout):
            return io.BytesIO(b'{"id":999,"name":"wrong"}')
        result=fetch_spell(133,"fake-token",opener=opener,sleeper=lambda _:None)
        self.assertEqual(result["status"],"invalid_response")

    def test_spell_response_can_parse_localized_string(self):
        def opener(request,timeout):
            return io.BytesIO('{"id":133,"name":"화염구"}'.encode("utf-8"))
        result=fetch_spell(133,"fake-token",opener=opener,sleeper=lambda _:None)
        self.assertEqual(result,{"spell_id":133,"status":"found","name_ko":"화염구"})

    def test_spell_404_is_missing_not_wrong_name(self):
        def opener(request,timeout):
            raise HTTPError(request.full_url,404,"Not Found",{},None)
        result=fetch_spell(133,"fake-token",opener=opener,sleeper=lambda _:None)
        self.assertEqual(result["status"],"not_found")

    def test_spell_401_is_fatal_no_false_verification(self):
        def opener(request,timeout):
            raise HTTPError(request.full_url,401,"Unauthorized",{},None)
        with self.assertRaises(RuntimeError):
            fetch_spell(133,"fake-token",opener=opener,sleeper=lambda _:None)

    def test_snapshot_unique_ids_and_locale(self):
        def opener(request,timeout):
            sid=int(request.full_url.split("/spell/")[1].split("?")[0])
            return io.BytesIO(json.dumps({"id":sid,"name":"예시"}).encode("utf-8"))
        result=fetch_snapshot([190319,133],"fake-token",opener=opener,
                              sleeper=lambda _:None,delay_seconds=0)
        self.assertEqual([x["spell_id"] for x in result["observations"]],[133,190319])
        self.assertEqual(result["locale"],"ko_KR")
        self.assertNotIn("fake-token",json.dumps(result))


    def test_official_icon_media_url_is_checked_and_provenance_kept(self):
        seen = []
        def opener(request, timeout):
            seen.append(request.full_url)
            if "/media/spell/" in request.full_url:
                return io.BytesIO(json.dumps({
                    "id": 133,
                    "assets": [{"key": "icon",
                                "value": "https://render.worldofwarcraft.com/kr/icons/56/spell_fire_fireball02.jpg"}]
                }).encode("utf8"))
            return io.BytesIO('{"id":133,"name":"화염구"}'.encode("utf8"))
        row = fetch_spell_media(133, "fake", opener=opener, sleeper=lambda _: None)
        self.assertEqual(row["status"], "found")
        self.assertTrue(row["icon_url"].startswith("https://render.worldofwarcraft.com/"))
        data = fetch_snapshot([133], "fake", opener=opener,
                              sleeper=lambda _: None, delay_seconds=0,
                              include_media=True)
        record = data["observations"][0]
        self.assertEqual(record["media"], row)
        self.assertIn("/data/wow/media/spell/133?", seen[-1])
        audited = audit(snapshot=data)
        result = next(x for x in audited["records"] if x["spell_id"] == 133)
        self.assertEqual(result["icon_review"], "pending")
        self.assertFalse(audited["publish_ready"])
        self.assertNotIn("fake", json.dumps(data))

    def test_official_icon_does_not_trust_unapproved_cdn_or_html(self):
        for url in (
            "https://example.com/kr/icons/56/example.jpg",
            "http://render.worldofwarcraft.com/kr/icons/56/example.jpg",
            "https://render.worldofwarcraft.com/kr/icons/56/example.jpg?token=abc",
            "javascript:alert(1)",
        ):
            def opener(request,timeout):
                return io.BytesIO(json.dumps({
                    "id": 133, "assets": [{"key": "icon", "value": url}],
                }).encode("utf8"))
            self.assertEqual(
                fetch_spell_media(133, "fake", opener=opener,
                                  sleeper=lambda _: None)["status"],
                "untrusted_icon_url",
            )

    def test_official_icon_media_unavailable_keeps_name_and_review(self):
        def opener(request,timeout):
            if "/media/spell/" in request.full_url:
                raise HTTPError(request.full_url, 404, "Not Found", {}, None)
            return io.BytesIO('{"id":133,"name":"화염구"}'.encode("utf8"))
        data = fetch_snapshot([133], "fake", opener=opener,
                              sleeper=lambda _: None, delay_seconds=0,
                              include_media=True)
        self.assertEqual(data["observations"][0]["status"], "found")
        self.assertEqual(data["observations"][0]["media"]["status"], "not_found")
        self.assertFalse(audit(snapshot=data)["publish_ready"])

    def test_untrusted_icon_in_snapshot_rejected_before_audit(self):
        data=snapshot([{
            "spell_id": 133, "status": "found", "name_ko": "화염구",
            "media": {"status": "found", "icon_url": "https://evil.test/icon.jpg"}
        }])
        with self.assertRaises(ValueError):
            audit(snapshot=data)


    def test_new_specialization_ids_can_be_verified_without_v11_inventory(self):
        unknown=1234567
        data=snapshot([{
            "spell_id":unknown, "status":"found", "name_ko":"신규 전문화 주문",
            "media":{"status":"found","icon_url":
                     "https://render.worldofwarcraft.com/kr/icons/56/spell_test.jpg"},
        }])
        with self.assertRaises(ValueError):
            audit(snapshot=data)
        result=audit(snapshot=data,additional_spell_ids={unknown})
        row=next(x for x in result["records"] if x["spell_id"]==unknown)
        self.assertEqual(row["comparison"],"new_spell_requires_editorial_review")
        self.assertEqual(row["inherited_names_ko"],[])
        self.assertEqual(row["official_icon_evidence"]["status"],"found")
        self.assertEqual(result["counts"]["new_spell_ids_without_inherited_label"],1)
        self.assertEqual(result["counts"]["new_spell_observations"],1)
        self.assertEqual(result["counts"]["official_names_auto_approved"],0)
        self.assertFalse(result["publish_ready"])

    def test_comma_separated_new_spell_ids_are_bounded_exact_and_unique(self):
        self.assertEqual(parse_spell_ids("5176,93402, 205636"),[5176,93402,205636])
        for value in ("", "123,", "abc", "1,1", "-3", "1;2", "0", "2147483648",
                      ",".join(str(x) for x in range(1,103))):
            with self.assertRaises(ValueError):
                parse_spell_ids(value)

    def test_no_credentials_fails_closed(self):
        with self.assertRaises(ValueError):
            oauth_token("","")


if __name__=="__main__":
    unittest.main()
