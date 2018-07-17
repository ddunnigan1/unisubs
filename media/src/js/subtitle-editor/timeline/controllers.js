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

    var module = angular.module('amara.SubtitleEditor.timeline.controllers', []);

    module.controller('TimelineController', ["$scope", "$timeout", "VideoPlayer", "MIN_DURATION", function($scope, $timeout, VideoPlayer, MIN_DURATION) {
        // Controls the scale of the timeline, currently we just set this to
        // 1.0 and leave it.
        $scope.scale = 1.0;
        // Video time info.
        $scope.currentTime = $scope.duration = null;
        // Subtitle at currentTime, or null.
        $scope.subtitle = null;
        $scope.showUpcomingUnsyncedSubtitle = false;
        /* Subtitles that we will sync when the user hits the up/down arrows.
         *
         * Contains the following properties:
         *    start - subtitle whose startTime will be synced
         *    end - subtitle whose endTime will be synced
         */

        var lastTimeReturned = null;
        var lastTimeReturnedAt = null;
        var lastTime = null;

        // Handle animating the timeline.  We don't use the timeupdate event
        // from popcorn because it doesn't fire granularly enough.
        var timeoutPromise = null;
        function startTimer() {
            if(timeoutPromise === null) {
                var delay = 30; // aim for 30 FPS or so
                timeoutPromise = $timeout(handleTimeout, delay, false);
            }
        }

        function cancelTimer() {
            if(timeoutPromise !== null) {
                $timeout.cancel(timeoutPromise);
                timeoutPromise = null;
            }
        }

        function handleTimeout() {
            updateTimeline();
            timeoutPromise = null;
            startTimer();
        }

        function updateTime() {
            var newTime = VideoPlayer.currentTime();
            // On the youtube player, popcorn only updates the time every 250
            // ms, which is not enough granularity for our animation.  Try to
            // get more granularity by starting a timer of our own.
            if(VideoPlayer.isPlaying()) {
                if(lastTimeReturned === newTime) {
                    var timePassed = Date.now() - lastTimeReturnedAt;
                    // If lots of time has bassed since the last new time, it's
                    // possible that the video is slowing down for some reason.
                    // Don't adjust the time too much.
                    timePassed = Math.min(timePassed, 500);
                    $scope.currentTime = newTime + timePassed;
                } else {
                    $scope.currentTime = newTime;
                    lastTimeReturnedAt = Date.now();
                    lastTimeReturned = newTime;
                }
            } else {
                $scope.currentTime = newTime;
                // Unset lastTimeReturned and lastTimeReturnedAt, we don't
                // want to tweak the time when the video is paused
                lastTimeReturned = lastTimeReturnedAt = null;
            }

            // If we adjust the time with the code above, then get a new time
            // from popcorn, it's possible that the time given will be less
            // that our adjusted time.  Try to fudge things a little so that
            // time doesn't go backwards while we're playing.
            if(lastTime !== null && $scope.currentTime < lastTime &&
                $scope.currentTime > lastTime - 250) {
                $scope.currentTime = lastTime;
            }
            lastTime = $scope.currentTime;
            $scope.timeline.currentTime = $scope.currentTime;
        }

        function unsyncedShown() {
            var lastSynced = $scope.workingSubtitles.subtitleList.lastSyncedSubtitle();
            return ((!lastSynced || lastSynced.endTime < $scope.currentTime) &&
                    $scope.workingSubtitles.subtitleList.firstUnsyncedSubtitle());
        }

        function updateUpcomingSubtitleSticker() {
            if (unsyncedShown()) {
                var s = $scope.workingSubtitles.subtitleList.secondUnsyncedSubtitle();
            } else {
                var s = $scope.workingSubtitles.subtitleList.firstUnsyncedSubtitle();
            }
            if (s) {
                // This is not good data binding but is kept consistent
                // with placement of subs on the timeline.
                // Using bind-html, we would keep the formatting.
                var span = $('span.upcomingUnsyncedSubtitleText');
                span.html(s.content());
                $scope.showUpcomingUnsyncedSubtitle = true;
            } else {
                $scope.showUpcomingUnsyncedSubtitle = false;
            }
        }

        function updateTimeline(redrawSubtitleOptions) {
            updateTime();
            updateUpcomingSubtitleSticker();
            $scope.redrawCanvas();
            $scope.redrawSubtitles(redrawSubtitleOptions);
        }

        function syncShownSubtitle() {
            if($scope.timeline.shownSubtitle !== $scope.selectedSubtitle) {
                $scope.selectSubtitle($scope.timeline.shownSubtitle);
            }
        }

        $scope.$root.$on('video-update', function(evt, updateType){
            $scope.duration = VideoPlayer.duration();
            $scope.timeline.duration = $scope.duration;
            updateTimeline();
            if(VideoPlayer.isPlaying()) {
                startTimer();
            } else {
                cancelTimer();
            }
            if(updateType == 'seek') {
                syncShownSubtitle();
            }
        });
        $scope.$root.$on('video-time-update', syncShownSubtitle);
        $scope.$root.$on("work-done", function() {
            updateTimeline({forcePlace: true});
        });

        function setSubtitleStartTime() {
            var subtitleList = $scope.workingSubtitles.subtitleList;
            var changes = [];
            var syncTime = $scope.currentTime;

            var subtitle = subtitleList.firstUnsyncedSubtitle();

            /* Check to see if we're setting the start time for the second
             * unsynced subtitle.  In this case, we should also set the end
             * time for the first.
             */
            if(subtitle.startTimeSynced()) {
                syncTime = Math.max(syncTime, subtitle.startTime + MIN_DURATION);
                changes.push({
                    subtitle: subtitle,
                    startTime: subtitle.startTime,
                    endTime: syncTime
                });

                subtitle = subtitleList.nextSubtitle(subtitle);
            }

            if(subtitle) {
                changes.push({
                    subtitle: subtitle,
                    startTime: syncTime,
                    endTime: -1
                });
            }

            subtitleList.updateSubtitleTimes(changes);
            $scope.$root.$emit("work-done");
        }
        // Sets the end of a subtitle at current position. If onlyUnsync is true
        // it only does it if the current endTime is unsynced, ie partially 
        // synced subtitle
        function setSubtitleEndTime() {
            var subtitleList = $scope.workingSubtitles.subtitleList;
            var subtitle = subtitleList.firstUnsyncedSubtitle();
            if (subtitle === null || !subtitle.startTimeSynced()) {
                return;
            }
            var syncTime = Math.max($scope.currentTime, subtitle.startTime +
                MIN_DURATION);
            subtitleList.updateSubtitleTime(subtitle, subtitle.startTime,
                syncTime);
            $scope.$root.$emit("work-done");
        }
        $scope.$root.$on('down-pressed', function($event) {
            if(unsyncedShown()) {
                setSubtitleStartTime();
                $event.preventDefault();
            }
        });
        $scope.$root.$on('up-pressed', function($event) {
            if(unsyncedShown()) {
                setSubtitleEndTime();
                $event.preventDefault();
            }
        });
    }]);
}).call(this);
