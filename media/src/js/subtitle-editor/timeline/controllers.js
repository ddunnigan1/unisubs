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

    module.controller('TimelineController', ["$scope", "$timeout", "VideoPlayer", "SubtitleSyncManager", "Keys", function($scope, $timeout, VideoPlayer, SubtitleSyncManager, Keys) {
        // Controls the scale of the timeline, currently we just set this to
        // 1.0 and leave it.
        $scope.scale = 1.0;
        // Video time info.
        $scope.currentTime = $scope.duration = null;
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
        var SubtitleSyncManager = new SubtitleSyncManager($scope);

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
            updateShownSubtitle();
            $scope.redrawSubtitles(redrawSubtitleOptions);
        }

        function updateShownSubtitle() {
            // First check if the current subtitle is still shown, this is
            // the most common case, and it's fast
            if($scope.timeline.shownSubtitle !== null &&
                $scope.timeline.shownSubtitle.isAt($scope.currentTime)) {
                return;
            }

            var shownSubtitle = $scope.workingSubtitles.subtitleList.subtitleAt(
                $scope.currentTime);
            if(shownSubtitle === null && $scope.unsyncedSubtitle !== null &&
                    $scope.unsyncedSubtitle.startTime <= $scope.currentTime) {
                shownSubtitle = $scope.unsyncedSubtitle.storedSubtitle;
            }
            $scope.timeline.shownSubtitle = shownSubtitle;
        }

        function syncShownSubtitle() {
            updateShownSubtitle();
            if($scope.timeline.shownSubtitle !== $scope.selectedSubtitle && !$scope.currentEdit.inProgress()) {
                $scope.selectSubtitle($scope.timeline.shownSubtitle);
            }
        }

        $scope.$root.$on('video-update', function(evt, updateType){
            $scope.duration = VideoPlayer.duration();
            $scope.timeline.duration = $scope.duration;
            updateTimeline();
            if(VideoPlayer.isPlaying()) {
                $scope.$emit('cancel-timeline-nudge');
                startTimer();
            } else {
                cancelTimer();
            }
            if(updateType == 'seek') {
                syncShownSubtitle();
            }
        });
        $scope.$root.$on('video-time-update', function() {
            updateTimeline();
            syncShownSubtitle()
        });
        $scope.$root.$on("work-done", function() {
            updateTimeline({forcePlace: true});
        });

        Keys.bind('no-edit', {
            'down': function() {
                if(unsyncedShown()) {
                    SubtitleSyncManager.syncUnsyncedStartTime();
                }
            },
            's': function() {
                SubtitleSyncManager.adjustClosestTiming();
            },
            'up': function() {
                if(unsyncedShown()) {
                    SubtitleSyncManager.syncUnsyncedEndTime();
                }
            }
        });
    }]);

    module.service('SubtitleSyncManager', ["MIN_DURATION", function(MIN_DURATION) {
        function SubtitleSyncManager($scope) {
            this.subtitleList = $scope.workingSubtitles.subtitleList;
            this.$scope = $scope;
        }

        SubtitleSyncManager.prototype = {
            syncUnsyncedStartTime: function() {
                var changes = [];
                var syncTime = this.$scope.currentTime;

                var subtitle = this.subtitleList.firstUnsyncedSubtitle();

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

                    subtitle = this.subtitleList.nextSubtitle(subtitle);
                }

                if(subtitle) {
                    changes.push({
                        subtitle: subtitle,
                        startTime: syncTime,
                        endTime: -1
                    });
                }

                this.subtitleList.updateSubtitleTimes(changes);
                this.$scope.$root.$emit("work-done");
            },
            // Sets the end of a subtitle at current position. If onlyUnsync is true
            // it only does it if the current endTime is unsynced, ie partially 
            // synced subtitle
            syncUnsyncedEndTime: function() {
                var subtitle = this.subtitleList.firstUnsyncedSubtitle();
                if (subtitle === null || !subtitle.startTimeSynced()) {
                    return;
                }
                var syncTime = Math.max(this.$scope.currentTime, subtitle.startTime +
                        MIN_DURATION);
                this.subtitleList.updateSubtitleTime(subtitle, subtitle.startTime,
                        syncTime);
                this.$scope.$root.$emit("work-done");
            },
            adjustClosestTiming: function() {
                var currentTime = this.$scope.currentTime;
                var subtitleList = this.subtitleList;
                var MAX_ADJUSTMENT = 1000;
                var $scope = this.$scope;

                function syncStartTime(subtitle) {
                    var changes = [];

                    if(Math.abs(subtitle.startTime - currentTime) > MAX_ADJUSTMENT) {
                        return;
                    }

                    changes.push({
                        subtitle: subtitle,
                        startTime: currentTime,
                        endTime: subtitle.endTime
                    });


                    var prevSubtitle = subtitleList.prevSubtitle(subtitle);

                    if(prevSubtitle && prevSubtitle.endTime == subtitle.startTime) {
                        changes.push({
                            subtitle: prevSubtitle,
                            startTime: prevSubtitle.startTime,
                            endTime: currentTime
                        });
                    }

                    subtitleList.updateSubtitleTimes(changes);
                    $scope.$root.$emit("work-done");
                }

                function syncEndTime(subtitle) {
                    var changes = [];

                    if(Math.abs(subtitle.endTime - currentTime) > MAX_ADJUSTMENT) {
                        return;
                    }

                    changes.push({
                        subtitle: subtitle,
                        startTime: subtitle.startTime,
                        endTime: currentTime
                    });

                    var nextSubtitle = subtitleList.nextSubtitle(subtitle);

                    if(nextSubtitle && nextSubtitle.startTime == subtitle.endTime) {
                        changes.push({
                            subtitle: nextSubtitle,
                            startTime: currentTime,
                            endTime: nextSubtitle.endTime
                        });
                    }

                    subtitleList.updateSubtitleTimes(changes);
                    $scope.$root.$emit("work-done");
                }

                var nextSubtitle = subtitleList.firstSubtitleAfter(currentTime);
                if(nextSubtitle) {
                    if(nextSubtitle.isAt(currentTime)) {
                        if(nextSubtitle.endTime - currentTime < currentTime - nextSubtitle.startTime) {
                            syncEndTime(nextSubtitle);
                        } else {
                            syncStartTime(nextSubtitle);
                        }
                    } else {
                        prevSubtitle = subtitleList.prevSubtitle(nextSubtitle);
                        if(prevSubtitle && currentTime - prevSubtitle.endTime < nextSubtitle.startTime - currentTime) {
                            syncEndTime(prevSubtitle);
                        } else {
                            syncStartTime(nextSubtitle);
                        }
                    }
                } else {
                    var prevSubtitle = subtitleList.lastSyncedSubtitle();
                    if(prevSubtitle) {
                        syncEndTime(prevSubtitle);
                    }
                }
            }
        }

        return SubtitleSyncManager;
    }]);
}).call(this);
