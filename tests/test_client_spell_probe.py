"""No-WoW-runtime smoke checks for optional client spell probe code."""
import re
import unittest
from engine.client_spell_probe import render_addon
from engine.spell_triage import analyze


class ClientSpellProbeTests(unittest.TestCase):
    def test_generated_lua_covers_exact_26_unresolved_ids(self):
        toc, lua=render_addon()
        ids = sorted(r["spell_id"] for r in analyze()["records"])
        block = lua.split("local ids = {",1)[1].split("}",1)[0]
        self.assertEqual(sorted(map(int,re.findall(r"\d+",block))),ids)
        self.assertEqual(len(ids),26)
        self.assertIn("## SavedVariables: WoWRotationSpellProbeDB",toc)
        self.assertIn("## Interface: 120105",toc)

    def test_uses_modern_static_spell_metadata_api(self):
        _,lua=render_addon()
        self.assertIn("C_Spell.GetSpellInfo",lua)
        self.assertIn("C_Spell.RequestLoadSpellData",lua)
        self.assertIn("SPELL_DATA_LOAD_RESULT",lua)
        self.assertIn('GetLocale() ~= "koKR"',lua)
        self.assertIn("SLASH_WOWROTATIONSPELLPROBE1",lua)
        self.assertIn("/wrspell",lua)
        self.assertIn("not_resolved_in_client",lua)

    def test_no_identity_combat_or_network_collection(self):
        _,lua=render_addon()
        for forbidden in ("UnitName(", "UnitGUID(", "GetRealmName(", "CombatLog",
                          "SendAddonMessage", "C_HTTP", "LoadURL", "GetPlayerMapPosition",
                          "GetAccountName", "GetCVar("):
            self.assertNotIn(forbidden,lua)
        self.assertEqual(render_addon(),render_addon())


if __name__=="__main__":
    unittest.main()
