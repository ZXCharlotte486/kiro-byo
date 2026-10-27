"""Display-only model name bridge for the KiroCrew 0.11.0-rc.1 dashboard.

Uses Crew 0.11's model row, composer chip, SettingsSelect and SettingsMultiSelect
DOM seams. Only BYO-owned chat dropdowns hide native Auto/Jev options;
settings keep their native Auto default. Display-only labels never change
model wire IDs, dropdown click handlers, API payloads or hashed JS assets.
Installation remains transactional via integration_manager backups.
"""
from __future__ import annotations

import json
from pathlib import Path

from .crew_dashboard_patch import DashboardAssetPatch, DashboardPatchError, type_label_map

MARKER = 'kiro-byo:crew11-type-labels:v1'
START = '<!-- ' + MARKER + ' -->'
END = '<!-- /' + MARKER + ' -->'
PREFIX = 'kiro-byo-type:'


def display_labels() -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for wire, names in type_label_map().items():
        if not wire.startswith(PREFIX):
            continue
        mode = wire[len(PREFIX):].split(':', 1)[0]
        # Prefer the product name from the pack, not its machine identifier.
        full = str(names.get('full') or '')
        mode_name = full.split(' — ', 1)[0].strip() or mode.capitalize()
        short = str(names.get('type') or '').strip()
        if not short:
            continue
        result[wire] = {'short': short, 'full': f'{mode_name} · {short}',
                        'group': str(names.get('group') or '形态 · 可手动切换')}
    return result


def _script(labels: dict[str, dict[str, str]]) -> str:
    # Source-controlled policy files are data, not trusted HTML/JS.
    data = json.dumps(labels, ensure_ascii=False, sort_keys=True).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return '''  <script id="kiro-byo-crew11-model-labels">
  (function () {
    "use strict";
    var PREFIX = "kiro-byo-type:";
    var LABELS = __LABELS__;
    var TYPE = /^kiro-byo-type:([a-z0-9_-]+):([a-z0-9_-]+)$/;
    var observer;
    var queued = false;

    function title(word) { return String(word).split(/[-_]+/).map(function(s){
      return s ? s.charAt(0).toUpperCase() + s.slice(1) : "";
    }).filter(Boolean).join(" "); }
    function label(wire) {
      var found = TYPE.exec(wire);
      if (!found) return null;
      if (LABELS[wire]) return LABELS[wire];
      var type = title(found[2]) + " Type";
      return {short: type, full: title(found[1]) + " · " + type};
    }
    // The React row's data-model-id remains the raw selection key. Only its
    // human-readable text is changed, so onSelect(m.name) stays unchanged.
    function menuLabels() {
      var spans = document.querySelectorAll('[data-model-id^="' + PREFIX + '"]');
      for (var i = 0; i < spans.length; i++) {
        var span = spans[i];
        if (!span.closest('button[role="option"], [role="option"]')) continue;
        var wire = span.getAttribute('data-model-id') || '';
        var names = label(wire);
        if (!names) continue;
        if (span.childNodes.length === 1 && span.firstChild.nodeType === 3 &&
            span.firstChild.nodeValue !== names.short) {
          // No React element replacement; the click target and selection ID
          // remain exactly as authored by Crew.
          span.firstChild.nodeValue = names.short;
        }
      }
    }
    // Presentation-only grouping for the conversational picker. React keeps its
    // original model IDs and onSelect closures. Never touch a Settings, task or
    // agent picker: the live composer + a Type row in this exact list define
    // our scope.
    function decorateConversationPickers() {
      var marked = document.querySelectorAll('[data-kiro-byo-crew11-auto], [data-kiro-byo-crew11-type-first], [data-kiro-byo-crew11-model-first]');
      for (var m = 0; m < marked.length; m++) {
        var row = marked[m];
        if (row.hasAttribute('data-kiro-byo-crew11-auto')) {
          row.removeAttribute('data-kiro-byo-crew11-auto');
          if (row.hasAttribute('data-kiro-byo-owned-inert')) { row.removeAttribute('inert'); row.removeAttribute('data-kiro-byo-owned-inert'); }
          if (row.hasAttribute('data-kiro-byo-owned-hidden')) { row.removeAttribute('aria-hidden'); row.removeAttribute('data-kiro-byo-owned-hidden'); }
        }
        row.removeAttribute('data-kiro-byo-crew11-type-first');
        row.removeAttribute('data-kiro-byo-crew11-model-first');
        row.removeAttribute('data-kiro-byo-crew11-group-label');
      }
      if (!document.querySelector('[data-testid="composer-model-chip"]')) return;
      // In this Crew version the model list is a flex column of sibling role=option
      // buttons; do not assume a generic dialog or hide Auto in other lists.
      var types = document.querySelectorAll('button[role="option"] [data-model-id^="' + PREFIX + '"]');
      var done = [];
      for (var t = 0; t < types.length; t++) {
        var firstRow = types[t].closest('button[role="option"]');
        var list = firstRow && firstRow.parentElement;
        if (!list || done.indexOf(list) >= 0) continue;
        done.push(list);
        var rows = list.querySelectorAll(':scope > button[role="option"]');
        var firstType = null, firstModel = null, hasType = false;
        for (var i = 0; i < rows.length; i++) {
          var span = rows[i].querySelector('[data-model-id]');
          if (!span) continue;
          var wire = span.getAttribute('data-model-id') || '';
          if (wire.indexOf(PREFIX) === 0) {
            hasType = true;
            if (!firstType) firstType = rows[i];
          } else if (wire === 'auto' || wire === 'auto:jev') {
            rows[i].setAttribute('data-kiro-byo-crew11-auto', '1');
            if (!rows[i].hasAttribute('inert')) { rows[i].setAttribute('inert', ''); rows[i].setAttribute('data-kiro-byo-owned-inert', '1'); }
            if (!rows[i].hasAttribute('aria-hidden')) { rows[i].setAttribute('aria-hidden', 'true'); rows[i].setAttribute('data-kiro-byo-owned-hidden', '1'); }
          } else if (hasType && !firstModel) {
            firstModel = rows[i];
          }
        }
        if (firstType) {
          var firstId = firstType.querySelector('[data-model-id]').getAttribute('data-model-id');
          var names = label(firstId);
          firstType.setAttribute('data-kiro-byo-crew11-type-first', '1');
          firstType.setAttribute('data-kiro-byo-crew11-group-label',
            (names && names.group) || '形态 · 可手动切换');
        }
        if (firstModel) firstModel.setAttribute('data-kiro-byo-crew11-model-first', '1');
      }
    }
    // Crew 0.11 Mate 2.0 uses one shared ModelField -> SimpleSelect for both
    // NewCrewmateDialog and CrewEditorModal. It has a stable uiLocation seam,
    // unlike SettingsSelect. Keep the underlying Radix option value untouched.
    // Never turn "继承" (inherit) into Tiga Multi: pin inheritance is meaningful.
    function mateLabelLeaves(root) {
      if (!root) return;
      var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      var n;
      while ((n = walker.nextNode())) {
        if (n.parentElement && n.parentElement.closest &&
            n.parentElement.closest('script,style,pre,code,textarea,input,[contenteditable]')) continue;
        exactMateLabel(n);
      }
    }
    function exactMateLabel(node) {
      if (!node || node.nodeType !== 3) return;
      var raw = node.nodeValue || '';
      var trimmed = raw.trim();
      var names = label(trimmed);
      if (names) node.nodeValue = raw.replace(trimmed, names.full);
    }
    function mateLabels() {
      var triggers = document.querySelectorAll('[data-ui-location="agents.model"]');
      for (var i = 0; i < triggers.length; i++) {
        var trigger = triggers[i];
        var role = trigger.getAttribute('role');
        if (role !== 'combobox' && trigger.tagName !== 'SELECT') continue;
        // Closed selection label, plus touch-native <option> text.
        mateLabelLeaves(trigger);
        if (trigger.tagName === 'SELECT') continue;
        // Radix renders choices in a body portal. Match only the listbox whose
        // ID belongs to THIS open Mate picker; never blanket-edit all portals.
        if (trigger.getAttribute('aria-expanded') !== 'true') continue;
        var listId = trigger.getAttribute('aria-controls');
        var listbox = listId && document.getElementById(listId);
        if (!listbox || listbox.getAttribute('role') !== 'listbox') continue;
        var choices = listbox.querySelectorAll('[role="option"]');
        for (var c = 0; c < choices.length; c++) mateLabelLeaves(choices[c]);
      }
    }
    // Settings -> Chat -> Model uses two separate components, not the shared
    // conversation ModelDropdownList. Keep Auto in Settings (Crew's global
    // fallback), preserve <option>.value and React's onChange model identity.
    // RC1's shipped translation keys (not arbitrary string substring matches).
    var defaultFieldNames = /^(默认模型|Default Model|Standardmodell|Modèle par défaut|Modelo predeterminado|デフォルトモデル|기본 모델|Modelo padrão|Модель по умолчанию|Modello predefinito|डिफ़ॉल्ट मॉडल|ডিফল্ট মডেল)$/i;
    var selectableFieldNames = /^(可选模型|Selectable Models|Auswählbare Modelle|Modèles sélectionnables|Modelos seleccionables|選択可能なモデル|선택 가능한 모델|Modelos selecionáveis|Модели в списке выбора|Modelli selezionabili|चुनने योग्य मॉडल|নির্বাচনযোগ্য মডেল)$/i;
    var settingsDefaultActive = false;
    function settingField(node, re) {
      var field = node && node.closest && node.closest('[data-setting-label]');
      return field && re.test(field.getAttribute('data-setting-label') || '') ? field : null;
    }
    function exactLabel(node, full) {
      if (!node || node.nodeType !== 3) return;
      var raw = node.nodeValue || '';
      var trimmed = raw.trim();
      var names = label(trimmed);
      if (names) node.nodeValue = raw.replace(trimmed, full ? names.full : names.short);
    }
    function settingsLabels() {
      // Collapsed default-model trigger (and native touch <select> options).
      var fields = document.querySelectorAll('[data-setting-label]');
      for (var f = 0; f < fields.length; f++) {
        if (!defaultFieldNames.test(fields[f].getAttribute('data-setting-label') || '')) continue;
        var choices = fields[f].querySelectorAll('[role="combobox"], select, option');
        for (var c = 0; c < choices.length; c++) {
          var walker = document.createTreeWalker(choices[c], NodeFilter.SHOW_TEXT);
          var n;
          while ((n = walker.nextNode())) exactLabel(n, true);
        }
      }
      // Radix portalled default-model options: process only while its trigger
      // opened the list (not other popovers which happen to contain Type ids).
      if (settingsDefaultActive) {
        var optionRows = document.querySelectorAll('[role="listbox"] [role="option"]');
        for (var r = 0; r < optionRows.length; r++) {
          var it = document.createTreeWalker(optionRows[r], NodeFilter.SHOW_TEXT);
          var text;
          while ((text = it.nextNode())) exactLabel(text, true);
        }
      }
      // MultiSelect has native checkbox keys in an isolated role=group. Only
      // change its text/accessible name; toggling remains value-keyed in React.
      var groups = document.querySelectorAll('[role="group"][aria-label]');
      for (var g = 0; g < groups.length; g++) {
        if (!selectableFieldNames.test(groups[g].getAttribute('aria-label') || '')) continue;
        var rows = groups[g].querySelectorAll('[data-multi-select-option]');
        for (var o = 0; o < rows.length; o++) {
          var input = rows[o].querySelector('input[aria-label],button[aria-label]');
          if (input) {
            var raw = input.getAttribute('aria-label') || '';
            var names = label(raw);
            if (names) input.setAttribute('aria-label', names.full);
          }
          var spans = rows[o].querySelectorAll('span');
          for (var j = 0; j < spans.length; j++) {
            if (spans[j].childNodes.length === 1 && spans[j].firstChild.nodeType === 3)
              exactLabel(spans[j].firstChild, true);
          }
        }
      }
    }
    document.addEventListener('pointerdown', function(evt) {
      settingsDefaultActive = !!settingField(evt.target, defaultFieldNames);
    }, true);
    document.addEventListener('focusin', function(evt) {
      if (settingField(evt.target, defaultFieldNames)) settingsDefaultActive = true;
    }, true);
    function replaceWire(text, pickShort) {
      return text.replace(/kiro-byo-type:[a-z0-9_-]+:[a-z0-9_-]+/g, function(wire) {
        var names = label(wire);
        return names ? (pickShort ? names.short : names.full) : wire;
      });
    }
    function safeTextNode(node) {
      if (!node || node.nodeType !== 3 || !node.parentElement) return false;
      var el = node.parentElement;
      if (el.closest('script,style,pre,code,textarea,input,[contenteditable],.prose,.markdown,.msg,[data-testid*="message"],[role="textbox"]')) return false;
      return true;
    }
    function visibleLabels() {
      // A live composer, status readout and model menu are only UI while the
      // BYO-selected chat is present. Never rewrite a user message or code.
      var chip = document.querySelector('[data-testid="composer-model-chip"]');
      if (chip) {
        var text = chip.querySelector('span.truncate');
        if (text && text.childNodes.length === 1 && text.firstChild.nodeType === 3) {
          var raw = text.firstChild.nodeValue || '';
          var display = replaceWire(raw, false);
          if (display !== raw) text.firstChild.nodeValue = display;
        }
        ['title', 'aria-label'].forEach(function (attr) {
          var raw = chip.getAttribute(attr) || '';
          var display = replaceWire(raw, false);
          if (display !== raw) chip.setAttribute(attr, display);
        });
      }
      // The 0.11 status bar and compact contextual model labels have no wire-id
      // data attribute. Update only exact-id text leaves, never user prose.
      if (!chip) return;
      var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      var node;
      while ((node = walker.nextNode())) {
        if (!safeTextNode(node)) continue;
        var raw = node.nodeValue || '';
        var exact = TYPE.test(raw.trim());
        if (!exact) {
          // Some Crew footer variants concatenate status and model into one
          // short text leaf. Only touch status/footer UI, never chat content.
          var el = node.parentElement;
          var rect = el.getBoundingClientRect ? el.getBoundingClientRect() : null;
          var low = !!(rect && rect.bottom > 0 && rect.bottom >= window.innerHeight - 64);
          if (raw.length > 160 || !raw.includes(PREFIX) ||
              !(el.closest('footer, [role="status"], [data-testid*="status"]') || low)) continue;
        }
        if (node.parentElement.closest('[data-model-id], [role="option"]')) continue;
        var full = replaceWire(raw, false);
        if (full !== raw) node.nodeValue = full;
      }
    }
    function apply() { queued = false; menuLabels(); decorateConversationPickers(); mateLabels(); settingsLabels(); visibleLabels(); }
    function schedule() {
      if (queued) return;
      queued = true;
      (window.requestAnimationFrame || function(fn){ return window.setTimeout(fn, 0); })(apply);
    }
    function relevant(record) {
      if (record.type === 'characterData') {
        var node = record.target;
        return !!(node.nodeValue && node.nodeValue.includes(PREFIX));
      }
      if (record.type === 'attributes') {
        var el = record.target;
        var value = el.getAttribute(record.attributeName) || '';
        return value.includes(PREFIX);
      }
      for (var i = 0; i < record.addedNodes.length; i++) {
        var item = record.addedNodes[i];
        if (item.nodeType === 3 && (item.nodeValue || '').includes(PREFIX)) return true;
        if (item.nodeType === 1 && (item.textContent || '').includes(PREFIX)) return true;
      }
      return false;
    }
    function start() {
      apply();
      observer = new MutationObserver(function(records) {
        for (var i = 0; i < records.length; i++) {
          if (relevant(records[i])) { schedule(); break; }
        }
      });
      observer.observe(document.body, {subtree:true, childList:true, characterData:true,
        attributes:true, attributeFilter:['title','aria-label','data-model-id']});
    }
    if (document.body) start();
    else document.addEventListener('DOMContentLoaded', start, {once:true});
  })();
  </script>
'''.replace('__LABELS__', data)


def block(labels: dict[str, dict[str, str]] | None = None) -> str:
    return '  ' + START + '\n' + _script(display_labels() if labels is None else labels) + '  <style id="kiro-byo-crew11-picker-groups">\n    button[data-kiro-byo-crew11-auto="1"] { display: none !important; }\n    button[data-kiro-byo-crew11-type-first="1"],\n    button[data-kiro-byo-crew11-model-first="1"] { position: relative; }\n    button[data-kiro-byo-crew11-type-first="1"] { margin-top: 22px; }\n    button[data-kiro-byo-crew11-model-first="1"] { margin-top: 32px; }\n    button[data-kiro-byo-crew11-type-first="1"]::before,\n    button[data-kiro-byo-crew11-model-first="1"]::before {\n      content: attr(data-kiro-byo-crew11-group-label);\n      position: absolute; left: 0; right: 0; display: block;\n      pointer-events: none; text-align: left;\n      font-size: 11px; font-weight: 600; line-height: 16px; color: var(--muted, #777);\n    }\n    button[data-kiro-byo-crew11-type-first="1"]::before { top: -20px; }\n    button[data-kiro-byo-crew11-model-first="1"]::before {\n      content: "具体模型 · 固定使用";\n      top: -28px; padding-top: 6px;\n      border-top: 1px dashed var(--border-strong, var(--border, #bbb));\n    }\n  </style>\n' + '  ' + END + '\n'


def _bundle_contract(dist: Path) -> None:
    if not dist.is_dir() or not (dist / 'index.html').is_file():
        raise DashboardPatchError('Crew 0.11 dashboard index.html is missing')
    has_row = False
    has_chip = False
    has_setting_field = False
    has_selectable_row = False
    has_mate_model = False
    for asset in sorted(dist.rglob('*.js')):
        if not asset.is_file():
            continue
        source = asset.read_text(encoding='utf-8', errors='ignore')
        has_row |= 'data-model-id' in source
        has_chip |= 'composer-model-chip' in source
        has_setting_field |= 'data-setting-label' in source
        has_selectable_row |= 'data-multi-select-option' in source
        has_mate_model |= 'agents.model' in source
        if has_row and has_chip and has_setting_field and has_selectable_row and has_mate_model:
            break
    if not (has_row and has_chip and has_setting_field and has_selectable_row and has_mate_model):
        raise DashboardPatchError('Crew 0.11 model UI contract unavailable (data-model-id / composer-model-chip / data-setting-label / data-multi-select-option / agents.model)')


def discover_dashboard_patches(crew_package: Path) -> list[DashboardAssetPatch]:
    dist = crew_package / 'static' / 'dist'
    _bundle_contract(dist)
    index = dist / 'index.html'
    original = index.read_text(encoding='utf-8')
    replacement = block()
    if START in original or END in original:
        if original.count(START) != 1 or original.count(END) != 1:
            raise DashboardPatchError('Crew 0.11 BYO label guard markers are incomplete or duplicated')
        start = original.index(START)
        # Previous markers are BYO-owned and already uniqueness-checked. A
        # minified index may have no newline before the marker.
        if original[max(0, start - 2):start] == '  ':
            start -= 2
        end = original.index(END) + len(END)
        if original[end:end + 1] == '\n':
            end += 1
        patched = original[:start] + replacement + original[end:]

    else:
        import re
        heads = list(re.finditer(r'</head\s*>', original, re.IGNORECASE))
        if len(heads) != 1:
            raise DashboardPatchError('Crew 0.11 dashboard requires one </head>')
        pos = heads[0].start()
        patched = original[:pos] + replacement + original[pos:]
    return [DashboardAssetPatch(index, original, patched, original != patched)]
