describe('SubtitleSyncManager', function() {
    var subtitleList, $scope, subtitles, syncManager;

    beforeEach(module('amara.SubtitleEditor.timeline.controllers'));
    beforeEach(module('amara.SubtitleEditor.subtitles.models'));
    beforeEach(module('amara.SubtitleEditor.mocks'));

    beforeEach(inject(function(SubtitleList) {
        subtitleList = new SubtitleList();
        subtitleList.loadEmptySubs('en');
        for(var i = 0; i < 5; i++) {
            var sub = subtitleList.insertSubtitleBefore(null);
            subtitleList.updateSubtitleContent(sub, 'subtitle ' + i);
            subtitleList.updateSubtitleTime(sub, i * 1000, i * 1000 + 500);
        }
        // Insert a bunch of unsynced subs
        for(var i = 0; i < 5; i++) {
            subtitleList.insertSubtitleBefore(null);
        }
        subtitles = subtitleList.subtitles;
    }));

    beforeEach(inject(function($rootScope, SubtitleSyncManager) {
        $scope = $rootScope;
        $scope.workingSubtitles = {
            subtitleList: subtitleList,
        }
        syncManager = new SubtitleSyncManager($scope);
    }));

    describe('syncing end times', function() {
        var subtitle;
        beforeEach(function() {
            spyOn(subtitleList, 'updateSubtitleTime').and.callThrough();
            subtitle = subtitleList.firstUnsyncedSubtitle();
        });

        it("sets the end time of the first unsynced subtitle", function() {
            subtitleList.updateSubtitleTime(subtitle, 10000, -1);
            $scope.currentTime = 11000;
            subtitleList.updateSubtitleTime.calls.reset();
            syncManager.syncUnsyncedEndTime();

            expect(subtitleList.updateSubtitleTime).toHaveBeenCalledWith(subtitle, 10000, 11000);
        });

        it("doesn't set the end time if no start time is set", function() {
            syncManager.syncUnsyncedEndTime();
            expect(subtitleList.updateSubtitleTime).not.toHaveBeenCalled();
        });

        it("respects MIN_DURATION", function() {
            subtitleList.updateSubtitleTime(subtitle, 10000, -1);
            $scope.currentTime = 10001;
            subtitleList.updateSubtitleTime.calls.reset();
            syncManager.syncUnsyncedEndTime();

            expect(subtitleList.updateSubtitleTime).toHaveBeenCalledWith(subtitle, 10000, 10250);
        });

    });

    describe('syncing start times', function() {
        var firstSubtitle, secondSubtitle;
        beforeEach(function() {
            spyOn(subtitleList, 'updateSubtitleTimes').and.callThrough();
            firstSubtitle = subtitleList.firstUnsyncedSubtitle();
            secondSubtitle = subtitleList.secondUnsyncedSubtitle();
        });

        it("sets the start time of the first unsynced subtitle", function() {
            $scope.currentTime = 10000;
            syncManager.syncUnsyncedStartTime();
            expect(subtitleList.updateSubtitleTimes).toHaveBeenCalledWith([
                    {
                        subtitle: firstSubtitle,
                        startTime: 10000,
                        endTime: -1
                    }
            ]);
        });

        describe('down key when the first unsynced subtitle has a start time set', function() {
            beforeEach(function() {
                subtitleList.updateSubtitleTime(firstSubtitle, 10000, -1);
            });

            it("sets the start time of the second unsynced subtitle and the end time of the first unsynced subtitle", function() {
                $scope.currentTime = 11000;
                syncManager.syncUnsyncedStartTime();
                expect(subtitleList.updateSubtitleTimes).toHaveBeenCalledWith([
                        {
                            subtitle: firstSubtitle,
                            startTime: 10000,
                            endTime: 11000,
                        },
                        {
                            subtitle: secondSubtitle,
                            startTime: 11000,
                            endTime: -1
                        }
                ]);
            });

            it("respects MIN_DURATION when setting end times", function() {
                $scope.currentTime = 10001;
                syncManager.syncUnsyncedStartTime();
                expect(subtitleList.updateSubtitleTimes).toHaveBeenCalledWith([
                        {
                            subtitle: firstSubtitle,
                            startTime: 10000,
                            endTime: 10250
                        },
                        {
                            subtitle: secondSubtitle,
                            startTime: 10250,
                            endTime: -1
                        }
                ]);
            });


            it("sets the end time only if there are no other unsynced subtitles", function() {
                $scope.currentTime = 11000;
                while(true) {
                    var nextSubtitle = subtitleList.nextSubtitle(firstSubtitle);
                    if(nextSubtitle) {
                        subtitleList.removeSubtitle(nextSubtitle);
                    } else {
                        break;
                    }
                }
                syncManager.syncUnsyncedStartTime();
                expect(subtitleList.updateSubtitleTimes).toHaveBeenCalledWith([
                        {
                            subtitle: firstSubtitle,
                            startTime: 10000,
                            endTime: 11000,
                        }
                ]);
            });
        });
    });

    describe('adjusting already synced subtitles', function() {
        beforeEach(function() {
            spyOn(subtitleList, 'updateSubtitleTimes').and.callThrough();
            firstSubtitle = subtitleList.firstUnsyncedSubtitle();
            secondSubtitle = subtitleList.secondUnsyncedSubtitle();
        });

        it("syncs the closest start/end time to the current time", function() {
            // moving start time forward
            $scope.currentTime = 1050;
            syncManager.adjustClosestTiming();
            expect(subtitleList.updateSubtitleTimes).toHaveBeenCalledWith([
                    {
                        subtitle: subtitles[1],
                        startTime: 1050,
                        endTime: 1500,
                    }
            ]);

            // moving end time forward
            subtitleList.updateSubtitleTimes.calls.reset();
            $scope.currentTime = 1550;
            syncManager.adjustClosestTiming();
            expect(subtitleList.updateSubtitleTimes).toHaveBeenCalledWith([
                    {
                        subtitle: subtitles[1],
                        startTime: 1050,
                        endTime: 1550,
                    }
            ]);

            // moving start time backward
            subtitleList.updateSubtitleTimes.calls.reset();
            $scope.currentTime = 950;
            syncManager.adjustClosestTiming();
            expect(subtitleList.updateSubtitleTimes).toHaveBeenCalledWith([
                    {
                        subtitle: subtitles[1],
                        startTime: 950,
                        endTime: 1550,
                    }
            ]);

            // moving end time backward
            subtitleList.updateSubtitleTimes.calls.reset();
            $scope.currentTime = 1450;
            syncManager.adjustClosestTiming();
            expect(subtitleList.updateSubtitleTimes).toHaveBeenCalledWith([
                    {
                        subtitle: subtitles[1],
                        startTime: 950,
                        endTime: 1450,
                    }
            ]);
        });

        it("doesn't sync if there is no timing within 1 second", function() {
            subtitleList.removeSubtitle(subtitles[2]);
            subtitleList.removeSubtitle(subtitles[1]);

            $scope.currentTime = 1999;
            syncManager.adjustClosestTiming();
            expect(subtitleList.updateSubtitleTimes).not.toHaveBeenCalled();

            $scope.currentTime = 1501;
            syncManager.adjustClosestTiming();
            expect(subtitleList.updateSubtitleTimes).not.toHaveBeenCalled();
        });

        it("syncs both start and end times if they're touching", function() {
            subtitleList.updateSubtitleTime(subtitles[0], 0, 1000);

            $scope.currentTime = 1050;
            syncManager.adjustClosestTiming();
            expect(subtitleList.updateSubtitleTimes).toHaveBeenCalledWith([
                    {
                        subtitle: subtitles[1],
                        startTime: 1050,
                        endTime: 1500
                    },
                    {
                        subtitle: subtitles[0],
                        startTime: 0,
                        endTime: 1050
                    }
            ]);
        });
    });

});

