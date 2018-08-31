/*
 * Amara, universalsubtitles.org
 *
 * Copyright (C) 2018 Participatory Culture Foundation
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see
 * http://www.gnu.org/licenses/agpl-3.0.html.
 */


var angular = angular || null;

(function() {
    var module = angular.module('amara.SubtitleEditor.keys', []);

    // Map key codes to special characters, copied from mousestrap
    // (https://github.com/ccampbell/mousetrap/)
    var specialKeyMap = {
        8: 'backspace',
        9: 'tab',
        13: 'enter',
        20: 'capslock',
        27: 'escape',
        32: 'space',
        33: 'pageup',
        34: 'pagedown',
        35: 'end',
        36: 'home',
        37: 'left',
        38: 'up',
        39: 'right',
        40: 'down',
        45: 'ins',
        46: 'del',
        91: 'meta',
        93: 'meta',
        106: '*',
        107: '+',
        109: '-',
        110: '.',
        111 : '/',
        186: ';',
        187: '=',
        188: ',',
        189: '-',
        190: '.',
        191: '/',
        192: '`',
        219: '[',
        220: '\\',
        221: ']',
        222: '\'',
        224: 'meta'
    };

    var modifierNames = [
        "ctrl",
        "alt",
        "shift",
    ];

    /*
     * Keys: Manage keyboard bindings.
     *
     * Use Keys.bind(context, bindings) to add key bindings.  context specifies
     * when the bindings are active (see below for more).  Bindings is an
     * object that maps key combinations like "ctrl c" to functions to invoke
     * then that binding is pressed.
     *
     * Keys are specified as "mod1 mod2 ... key".  Mods can be:
     *    - "ctrl" -- Control key (also command on OSX)
     *    - "alt"  -- Alt key
     *    - "shift -- Shift key
     *
     * Contexts allow us to conditionally enable/disable bindings.  For
     * example, we want to support left/right to "nudge" subtitle timings, but
     * only when the user has clicked on the subtitle in the timeline.
     *
     * When you add bindings you specify a context.  The "default" context is
     * always enabled.  Other contexts are disabled by default, but can be
     * enabled using Keys.enableContext().  Non-default contexts override the
     * default context if they bind the same key.  Use Keys.disableContext() to
     * disable bindings once a context is no longer active.
     */
    module.factory("Keys", ["$document", "runningOnOSX", function($document, runningOnOSX){
        var globalDisable = false;
        var enabledContexts = [];

        $document = $($document); // Get a JQuery element rather than JQuery-lite

        // Handle normalizing key strings
        function parseKeyString(keyString) {
            var keyName = null;
            var modifiers = {};
            _.each(keyString.split(' '), function(keyPart) {
                if(keyPart == '') {
                    return;
                } else if(modifierNames.indexOf(keyPart) != -1) {
                    modifiers[keyPart] = true;
                } else {
                    if(keyName !== null) {
                        throw "Error parsing keybinding: " + keyString;
                    }
                    keyName = keyPart;
                }
            });
            if(keyName === null) {
                throw "Error parsing keybinding: " + keyString;
            }
            return makeKeyString(keyName, modifiers);
        }

        function keyStringFromEvent(evt) {
            var keyName;
            var modifiers = {};

            if(evt.ctrlKey) {
                modifiers.ctrl = true;
            }
            if(evt.altKey) {
                modifiers.alt = true;
            }
            if(evt.shiftKey) {
                modifiers.shift = true;
            }
            if(evt.metaKey && runningOnOSX()) {
                modifiers.ctrl = true;
            }

            if(evt.which in specialKeyMap) {
                keyName = specialKeyMap[evt.which];
            } else {
                keyName = String.fromCharCode(evt.which).toLowerCase();
            }
            return makeKeyString(keyName, modifiers);
        }

        function makeKeyString(keyName, modifiers) {
            var parts = [];
            _.each(modifierNames, function(modName) {
                if(modifiers[modName]) {
                    parts.push(modName);
                }
            });
            parts.push(keyName);
            return parts.join(' ');
        }

        // Map context to another map that maps key strings to functions
        var allBindings = {
            "default": {}
        };

        $document.on('keydown', function(evt) {
            if(globalDisable) {
                return;
            }
            var keyString = keyStringFromEvent(evt);
            trigger(keyString, evt);
        });

        function trigger(keyString, evt) {
            var context = _.find(enabledContexts, function(context) {
                return allBindings[context][keyString];
            });
            if(context === undefined) {
                context = 'default';
            }
            var callback = allBindings[context][keyString];

            if(callback) {
                var rv = callback();
                if(rv !== true && evt) {
                    evt.preventDefault();
                }
            }
        }


        function bind(context, bindings) {
            if(allBindings[context] === undefined) {
                allBindings[context] = {};
            }
            _.extend(allBindings[context], normalizeBindings(bindings));
        }

        function normalizeBindings(bindings) {
            var normalized = {};
            _.each(bindings, function(callback, fullKeyString) {
                _.each(fullKeyString.split('|'), function(keyString) {
                    keyString = keyString.trim();
                    normalized[parseKeyString(keyString)] = callback;
                });
            });
            return normalized;
        }

        function enableContext(context) {
            if(enabledContexts.indexOf(context) == -1) {
                enabledContexts.push(context);
            }
        }

        function disableContext(context) {
            var pos = enabledContexts.indexOf(context);
            if(pos != -1) {
                enabledContexts.splice(pos, 1);
            }
        }

        return {
            bind: bind,
            trigger: trigger,
            disable: function() { globalDisable = true; },
            enable: function() { globalDisable = false; },
            enableContext: enableContext,
            disableContext: disableContext
        };
    }]);
}).call(this);
