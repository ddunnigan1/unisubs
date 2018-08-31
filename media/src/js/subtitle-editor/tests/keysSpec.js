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

describe("The Keys service", function() {
    var $document;
    var Keys;
    var callback;
    var runningOnOSX;
    var A_KEYCODE = 65;
    var B_KEYCODE = 66;
    var ENTER_KEYCODE = 13;

    beforeEach(module('amara.SubtitleEditor.mocks'));
    beforeEach(module('amara.SubtitleEditor.keys'));

    beforeEach(inject(function($injector) {
        $document = $($injector.get('$document'));
        Keys = $injector.get('Keys');
        callback = jasmine.createSpy('keyBindingCallback');
        runningOnOSX = $injector.get('runningOnOSX');
        runningOnOSX.and.returnValue(false);
    }));

    function triggerKey(keyCode, attrs) {
        if(attrs == undefined) {
            attrs = {};
        }
        var evt = $.Event('keydown', {
            keyCode: keyCode,
            which: keyCode,
            ctrlKey: Boolean(attrs.ctrlKey),
            shiftKey: Boolean(attrs.shiftKey),
            altKey: Boolean(attrs.altKey),
            metaKey: Boolean(attrs.metaKey)
        });
        $document.trigger(evt);
        return evt;
    }

    it("binds keys to callbacks", function() {
        Keys.bind('default', {
            'a': callback,
        });
        triggerKey(A_KEYCODE);
        expect(callback).toHaveBeenCalled();
    });

    it("binds multiple keys to a single callback", function() {
        Keys.bind('default', {
            'a | b': callback,
        });
        triggerKey(A_KEYCODE);
        expect(callback).toHaveBeenCalled();

        callback.calls.reset();
        triggerKey(B_KEYCODE);
        expect(callback).toHaveBeenCalled();
    });

    it("handles special keys", function() {
        Keys.bind('default', {
            'enter': callback,
        });
        triggerKey(ENTER_KEYCODE);
        expect(callback).toHaveBeenCalled();
    });

    it("handles modifier keys", function() {
        Keys.bind('default', {
            'ctrl a': callback,
        });
        triggerKey(A_KEYCODE);
        expect(callback).not.toHaveBeenCalled();

        triggerKey(A_KEYCODE, {ctrlKey: true});
        expect(callback).toHaveBeenCalled();
    });

    it("handles modifier keys in any order", function() {
        Keys.bind('default', {
            'ctrl shift a': callback,
            'shift ctrl b': callback,
        });
        triggerKey(A_KEYCODE, {ctrlKey: true, shiftKey: true});
        expect(callback).toHaveBeenCalled();

        callback.calls.reset();
        triggerKey(B_KEYCODE, {ctrlKey: true, shiftKey: true});
        expect(callback).toHaveBeenCalled();
    });

    it("doesn't invoke callbacks if extra modifier keys are present", function() {
        Keys.bind('default', {
            'ctrl shift a': callback,
            'shift ctrl b': callback,
        });
        triggerKey(A_KEYCODE, {shiftKey: true});
        expect(callback).not.toHaveBeenCalled();

        triggerKey(A_KEYCODE, {ctrlKey: true});
        expect(callback).not.toHaveBeenCalled();
    });

    it("calls preventDefault, unless the function returns true", function() {
        Keys.bind('default', {
            'a': callback,
        });
        var evt = triggerKey(A_KEYCODE);
        expect(evt.isDefaultPrevented()).toBeTruthy();

        callback.and.returnValue(true);
        var evt = triggerKey(A_KEYCODE);
        expect(evt.isDefaultPrevented()).toBeFalsy();
    });

    it("manually triggers keys", function() {
        Keys.bind('default', {
            'ctrl a': callback,
        });
        Keys.trigger('ctrl a');
        expect(callback).toHaveBeenCalled();
    });


    it("raises an exception on invalid keys", function() {
        // Invalid modifier
        expect(function() { Keys.bind('default', { 'foo a': callback, })}).toThrow("Error parsing keybinding: foo a");
        // Multiple keys
        expect(function() { Keys.bind('default', { 'a b': callback, })}).toThrow("Error parsing keybinding: a b");
        // No key
        expect(function() { Keys.bind('default', { 'ctrl': callback, })}).toThrow("Error parsing keybinding: ctrl");
    });

    it("can be disabled", function() {
        Keys.bind('default', {
            'a': callback,
        });
        Keys.disable();
        triggerKey(A_KEYCODE);
        expect(callback).not.toHaveBeenCalled();

        Keys.enable();
        triggerKey(A_KEYCODE);
        expect(callback).toHaveBeenCalled();
    });

    describe('command and control handling', function() {
        it("allows using meta (command) instead of ctrl on OSX", function() {
            runningOnOSX.and.returnValue(true);
            Keys.bind('default', {
                'ctrl a': callback,
            });
            triggerKey(A_KEYCODE, {metaKey: true});
            expect(callback).toHaveBeenCalled();
        });

        it("allows using actual ctrl on OSX", function() {
            runningOnOSX.and.returnValue(true);
            Keys.bind('default', {
                'ctrl a': callback,
            });
            triggerKey(A_KEYCODE, {ctrlKey: true});
            expect(callback).toHaveBeenCalled();
        });

        it("doesn't allow using meta instead of control when not on OSX", function() {
            runningOnOSX.and.returnValue(false);
            Keys.bind('default', {
                'ctrl a': callback,
            });
            triggerKey(A_KEYCODE, {metaKey: true});
            expect(callback).not.toHaveBeenCalled();
        });
    });

    describe('Contexts', function() {
        beforeEach(function() {
            Keys.bind('test', {
                'a': callback,
            });
        });

        it("doesn't trigger bindings from non-default contexts by default", function() {
            triggerKey(A_KEYCODE);
            expect(callback).not.toHaveBeenCalled();
        });

        it("supports enabling contexts", function() {
            Keys.enableContext('test');
            triggerKey(A_KEYCODE);
            expect(callback).toHaveBeenCalled();
        });

        it("allows disabling contexts", function() {
            Keys.enableContext('test');
            Keys.disableContext('test');
            triggerKey(A_KEYCODE);
            expect(callback).not.toHaveBeenCalled();
        });

        it("prefers bindings from non-default contexts", function() {
            var callback2 = jasmine.createSpy('callback2');
            Keys.bind('default', {
                'a': callback2,
            });
            Keys.enableContext('test');
            triggerKey(A_KEYCODE);
            expect(callback).toHaveBeenCalled();
            expect(callback2).not.toHaveBeenCalled();
        });
    });
});
