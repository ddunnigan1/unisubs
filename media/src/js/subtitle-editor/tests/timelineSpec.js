describe('TimelineController', function() {
    var subtitleList = null;
    var $scope = null;
    var subtitles = [];
    var MIN_DURATION = null;
    var VideoPlayer = null;

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

    beforeEach(inject(function($controller, $rootScope, $injector) {
        $scope = $rootScope;
        $scope.timelineShown = true;
        $scope.timeline = {
            shownSubtitle: null,
            currentTime: null,
            duration: null
        };
        $scope.workflow = {
            stage: 'syncing'
        };
        $scope.selectSubtitle = jasmine.createSpy('selectSubtitle');
        $scope.workingSubtitles = {
            'subtitleList': subtitleList,
        }
        MIN_DURATION = 250;
        var controller = $controller('TimelineController', {
            $scope: $scope,
            MIN_DURATION: MIN_DURATION,
        });
        // in our tests, we make will sync happen by emitting work-done.  In
        // that case, the TimelineController also calls redrawSubtitles/redrawCanvas, so we
        // need to mock it.
        $scope.redrawCanvas = jasmine.createSpy('redrawCanvas');
        $scope.redrawSubtitles = jasmine.createSpy('redrawSubtitles');
        VideoPlayer = $injector.get('VideoPlayer');
    }));

    beforeEach(function() {
        jasmine.addMatchers({
            toHaveStartSub: function(util, customEqualityTesters) {
                return {
                    compare: function(actual, expected) {
                        var start = actual.calls.mostRecent().args[1].start;
                        return {
                            pass: util.equals(start, expected)
                        };
                    }
                };
            },
            toHaveEndSub: function(util, customEqualityTesters) {
                return {
                    compare: function(actual, expected) {
                        var end = actual.calls.mostRecent().args[1].end;
                        return {
                            pass: util.equals(end, expected)
                        };
                    }
                };
            }
        });
    });

    describe('syncing with the up key', function() {
        var subtitle;
        beforeEach(function() {
            spyOn(subtitleList, 'updateSubtitleTime').and.callThrough();
            subtitle = subtitleList.firstUnsyncedSubtitle();
        });

        it("sets the end time of the first unsynced subtitle", function() {
            subtitleList.updateSubtitleTime(subtitle, 10000, -1);
            $scope.currentTime = 11000;
            subtitleList.updateSubtitleTime.calls.reset();
            $scope.$emit('up-pressed');

            expect(subtitleList.updateSubtitleTime).toHaveBeenCalledWith(subtitle, 10000, 11000);
        });

        it("doesn't set the end time if no start time is set", function() {
            $scope.$emit('up-pressed');
            expect(subtitleList.updateSubtitleTime).not.toHaveBeenCalled();
        });

        it("respects MIN_DURATION", function() {
            subtitleList.updateSubtitleTime(subtitle, 10000, -1);
            $scope.currentTime = 10001;
            subtitleList.updateSubtitleTime.calls.reset();
            $scope.$emit('up-pressed');

            expect(subtitleList.updateSubtitleTime).toHaveBeenCalledWith(subtitle, 10000, 10250);
        });

        it("calls preventDefault", function() {
            subtitleList.updateSubtitleTime(subtitle, 10000, -1);
            $scope.currentTime = 10001;
            var evt = $scope.$emit('up-pressed');

            expect(evt.defaultPrevented).toBeTruthy();
        });

        it("does nothing if no unsynced subtitle is shown", function() {
            subtitleList.updateSubtitleTime(subtitle, 10000, -1);
            $scope.currentTime = 4000;
            subtitleList.updateSubtitleTime.calls.reset();
            var evt = $scope.$emit('up-pressed');

            expect(subtitleList.updateSubtitleTime).not.toHaveBeenCalled();
            expect(evt.defaultPrevented).toBeFalsy();
        });

    });

    describe('syncing with the down key', function() {
        var firstSubtitle, secondSubtitle;
        beforeEach(function() {
            spyOn(subtitleList, 'updateSubtitleTimes').and.callThrough();
            firstSubtitle = subtitleList.firstUnsyncedSubtitle();
            secondSubtitle = subtitleList.secondUnsyncedSubtitle();
        });

        it("sets the start time of the first unsynced subtitle", function() {
            $scope.currentTime = 10000;
            $scope.$emit('down-pressed');
            expect(subtitleList.updateSubtitleTimes).toHaveBeenCalledWith([
                    {
                        subtitle: firstSubtitle,
                        startTime: 10000,
                        endTime: -1
                    }
            ]);
        });

        it("calls preventDefault", function() {
            $scope.currentTime = 10000;
            var evt = $scope.$emit('down-pressed');
            expect(evt.defaultPrevented).toBeTruthy();
        });

        it("does nothing if no unsynced subtitle is shown", function() {
            $scope.currentTime = 4000;
            var evt = $scope.$emit('down-pressed');
            expect(subtitleList.updateSubtitleTimes).not.toHaveBeenCalled();
            expect(evt.defaultPrevented).toBeFalsy();
        });

        describe('down key when the first unsynced subtitle has a start time set', function() {
            beforeEach(function() {
                subtitleList.updateSubtitleTime(firstSubtitle, 10000, -1);
            });

            it("sets the start time of the second unsynced subtitle and the end time of the first unsynced subtitle", function() {
                $scope.currentTime = 11000;
                $scope.$emit('down-pressed');
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
                $scope.$emit('down-pressed');
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
                $scope.$emit('down-pressed');
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

});

