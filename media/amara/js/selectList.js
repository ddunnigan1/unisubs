/*
 * Amara, universalsubtitles.org
 *
 * Copyright (C) 2016 Participatory Culture Foundation
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

/*
 * selectList is used to handle a list of items connected to some popup forms.  When one or more items are selected, we pop open an actionBar. 
 * When one of the buttons on the actionBar is clicked, then we pop up a modal dialog.
 */


(function($) {
    $.behaviors('.selectList', selectList);

    function selectList(container) {
        var actionBar = $($(container).data('target'));
        var actions =$('.selectList-action', actionBar);
        var checkboxes = $('.selectList-checkbox', container);
        checkboxes.change(function() {
            if(checkboxes.is(':checked')) {
                actionBar.addClass('open');
            } else {
                actionBar.removeClass('open');
            }
            actions.data('selection', getSelection().join('-'));
        });

        function getSelection() {
            var selection = [];
            checkboxes.filter(":checked").each(function() {
                selection.push(this.value);
            });
            return selection;
        }
    }
})(jQuery);