// Amara, universalsubtitles.org
//
// Copyright (C) 2013 Participatory Culture Foundation
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as
// published by the Free Software Foundation, either version 3 of the
// License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see
// http://www.gnu.org/licenses/agpl-3.0.html.

(function() {

    var module = angular.module('amara.SubtitleEditor.help', []);

    module.controller('HelpController', ['$scope', '$sce', function($scope, $sce) {
        $scope.commands = [
            { key: 'tab', description: $sce.trustAsHtml('starts and stops video playback') },
            { key: 'enter', description: $sce.trustAsHtml('moves to the next line and <br /> adds a new line (when the timeline is closed)') },
            { key: 'shift + enter', description: $sce.trustAsHtml('adds a line break in the subtitle line') }
        ];

        $scope.showAdvancedModal = function() {
            throw "Not implemented";
        };

    }]);

    module.controller('KeyboardControlsController', ['$scope', function($scope) {
        $scope.keyboardControlsMode = function() {
            if($scope.$root.nudging) {
                return 'nudging';
            } else {
                return $scope.workflow.stage;
            }
        }
        $scope.hideUpDownArrows = function() {
            console.log($scope.workingSubtitles.subtitleList.isComplete());
            return $scope.workingSubtitles.subtitleList.isComplete();
        }
    }]);
}).call(this);
