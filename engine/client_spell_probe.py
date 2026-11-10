"""Generate a small optional retail WoW addon to check API-gap spell IDs.

The addon reads static C_Spell metadata only. It does NOT inspect combat,
character identity, UI secrets, coordinates, private logs or account data.
Generated files are optional, not a substitute for game-rule verification.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .spell_triage import analyze

ADDON = "WoWRotationSpellProbe"
INTERFACE = 120105


def render_addon() -> tuple[str, str]:
    queue = analyze()
    ids = sorted(r["spell_id"] for r in queue["records"])
    if len(ids) != 26 or len(ids) != len(set(ids)):
        raise ValueError("Expected exactly 26 unique review spell IDs")
    toc = (
        f"## Interface: {INTERFACE}\n"
        "## Title: WoW Rotation Spell Probe\n"
        "## Notes: Offline koKR spell ID cross-check (no combat data)\n"
        "## Author: WoW Rotation Engine\n"
        "## Version: 0.1.0\n"
        "## SavedVariables: WoWRotationSpellProbeDB\n"
        "SpellProbe.lua\n"
    )
    ids_lines = "\n".join(f"    {sid}," for sid in ids)
    lua = r'''-- Generated, optional koKR spell ID check. Never outputs private identifiers.
-- Pending/nil spell info is NOT proof that a spell is invalid.
local ADDON = ...
local ids = {
__IDS__
}
local pending = {}

local function store()
    if type(WoWRotationSpellProbeDB) ~= "table" then
        WoWRotationSpellProbeDB = {}
    end
    local db = WoWRotationSpellProbeDB
    db.schema = "client-spell-probe-v1"
    db.locale = GetLocale()
    db.interface = select(4, GetBuildInfo())
    if type(db.observations) ~= "table" then db.observations = {} end
    return db
end

local function observe(id, status, name)
    local db = store()
    local result = { status = status }
    if type(name) == "string" and name ~= "" then result.name_ko = name end
    db.observations[tostring(id)] = result
end

local function checkOne(id, request)
    if GetLocale() ~= "koKR" then
        observe(id, "wrong_client_locale")
        pending[id] = nil
        return
    end
    if type(C_Spell) ~= "table" or type(C_Spell.GetSpellInfo) ~= "function" then
        observe(id, "spell_api_unavailable")
        pending[id] = nil
        return
    end
    local ok, info = pcall(C_Spell.GetSpellInfo, id)
    if ok and type(info) == "table"
        and type(info.name) == "string" and info.name ~= "" then
        observe(id, "found", info.name)
        pending[id] = nil
        return
    end
    if request then
        observe(id, "awaiting_spell_data")
        pending[id] = true
        if type(C_Spell.RequestLoadSpellData) == "function" then
            pcall(C_Spell.RequestLoadSpellData, id)
        end
    else
        observe(id, "not_resolved_in_client")
        pending[id] = nil
    end
end

local function scan()
    local db = store()
    db.observations = {}
    pending = {}
    for _, id in ipairs(ids) do checkOne(id, true) end
    print("|cffdfbc7dWoW Rotation Spell Probe|r scanned " .. #ids .. " spell IDs.")
    print("Run /reload or log out to write SavedVariables to disk.")
end

local function summary()
    local db = store()
    local found, unresolved = 0, 0
    for _, row in pairs(db.observations) do
        if row.status == "found" then found = found + 1
        else unresolved = unresolved + 1 end
    end
    print("WoW Rotation Spell Probe: found=" .. found ..
        ", pending/unresolved=" .. unresolved .. ", locale=" .. tostring(db.locale))
end

SLASH_WOWROTATIONSPELLPROBE1 = "/wrspell"
SlashCmdList["WOWROTATIONSPELLPROBE"] = function(message)
    if message == "scan" then scan()
    else summary() end
end

local frame = CreateFrame("Frame")
frame:RegisterEvent("PLAYER_LOGIN")
frame:RegisterEvent("SPELL_DATA_LOAD_RESULT")
frame:SetScript("OnEvent", function(_, event, arg1, arg2)
    if event == "PLAYER_LOGIN" then
        scan()
    elseif event == "SPELL_DATA_LOAD_RESULT" and pending[arg1] then
        checkOne(arg1, false)
    end
end)
'''.replace("__IDS__", ids_lines)
    return toc, lua


def main() -> int:
    p = argparse.ArgumentParser(description="Generate an optional spell lookup addon")
    p.add_argument("--output", default="dist/WoWRotationSpellProbe")
    args = p.parse_args()
    toc, lua = render_addon()
    directory = Path(args.output)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{ADDON}.toc").write_text(toc, encoding="utf-8")
    (directory / "SpellProbe.lua").write_text(lua, encoding="utf-8")
    print(f"Generated optional koKR client addon: {directory} (26 IDs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
