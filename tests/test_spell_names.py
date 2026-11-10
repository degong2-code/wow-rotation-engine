"""No-network tests for Korean spell-name evidence and publication safety."""
import io
import json
from urllib.error import HTTPError
import unittest

from engine.spell_names import (
    audit, fetch_snapshot, fetch_spell, inventory, oauth_token,
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

    def test_no_credentials_fails_closed(self):
        with self.assertRaises(ValueError):
            oauth_token("","")


if __name__=="__main__":
    unittest.main()
