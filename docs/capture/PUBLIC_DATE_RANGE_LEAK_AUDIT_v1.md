# Public Date Range Leak Audit v1

Date: 2026-06-01

This audit catches capture-phase or collection-scope date ranges that must not be displayed as object or movement chronology.

## Summary

- Issues found: 0

## Rule

Broad ranges such as `1970-2026` are valid for capture planning or source collection scope only. Public sheets must use item-level dates, precise group ranges, or an explicit `undated/source scope` state.

## Sample

| Source | Record | Issue | Value | Title |
|---|---|---|---|---|
