describe('TimelineDrag', function() {
    var $scope;
    var $timeout;
    var subtitleList;
    var sub1, sub2, sub3;
    var VideoPlayer;
    var TimelineDrag;
    var dragHandler;
    var subtitleContainer;

    beforeEach(module('amara.SubtitleEditor.keys'));
    beforeEach(module('amara.SubtitleEditor.mocks'));
    beforeEach(module('amara.SubtitleEditor.subtitles.models'));
    beforeEach(module('amara.SubtitleEditor.timeline.directives'));

    beforeEach(inject(function($rootScope, $injector, SubtitleList) {
        $timeout = $injector.get('$timeout');
        VideoPlayer = $injector.get('VideoPlayer');
        TimelineDrag = $injector.get('TimelineDrag');
        subtitleList = new SubtitleList();
        subtitleList.loadEmptySubs('en');
        $scope = $rootScope;
        $scope.workingSubtitles = {
            subtitleList: subtitleList
        };
        $scope.currentTime = 0;
        $scope.duration = 4000;
        $scope.scale = 1; // 1 px == 10 ms
        $scope.selectSubtitle = jasmine.createSpy('selectSubtitle');

        subtitleContainer = $('<div/>');

        function makeSubtitle(startTime, endTime, content) {
            var subtitle = subtitleList._insertSubtitle(subtitleList.subtitles.length, {
                startTime: startTime,
                endTime: endTime,
                content: content
            });
            var div = $('<div class="subtitle">');
            var handleLeft = $('<div class="handle left">');
            var handleRight = $('<div class="handle right">');
            div.data('subtitle', subtitle);
            div.append(handleLeft);
            div.append(handleRight);
            subtitleContainer.append(div);

            return {
                subtitle: subtitle,
                div: div,
                handleLeft: handleLeft,
                handleRight: handleRight
            }
        }

        sub1 = makeSubtitle(0, 1000, 'sub1');
        sub2 = makeSubtitle(1000, 2000, 'sub2');
        sub3 = makeSubtitle(3000, 4000, 'sub3');
    }));

    function createHandler(handlerClass, subtitleDiv, clickTime) {
        if(clickTime === undefined) {
            clickTime = 0;
        }
        dragHandler = new handlerClass($scope, subtitleDiv, clickTime, 'testChangeGroup-');
    }

    describe('SubtitleDragHandlerMiddle', function() {
        it('moves subtitles', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub2.div);
            dragHandler.onDrag(200);
            expect(sub2.subtitle.getTimings()).toEqual([1200, 2200]);

            dragHandler.onDrag(100);
            expect(sub2.subtitle.getTimings()).toEqual([1100, 2100]);
        });

        it("uses a single changeGroup to allow undoing all changes at once", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub2.div);
            dragHandler.onDrag(1);
            dragHandler.onDrag(2);
            dragHandler.onDrag(3);
            dragHandler.onEnd();
            subtitleList.undo();
            expect(sub2.subtitle.getTimings()).toEqual([1000, 2000]);
        });

        it("doesn't move subtitles over other subtitles timings", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub2.div);
            dragHandler.onDrag(-1);
            expect(sub2.subtitle.getTimings()).toEqual([1000, 2000]);

            dragHandler.onDrag(1001);
            expect(sub2.subtitle.getTimings()).toEqual([2000, 3000]);
        });

        it("doesn't move subtitles before time=0", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub1.div);
            dragHandler.onDrag(-1);
            expect(sub1.subtitle.getTimings()).toEqual([0, 1000]);
        });

        it("doesn't move subtitles after time=scope.duration", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub3.div);
            dragHandler.onDrag(1);
            expect(sub3.subtitle.getTimings()).toEqual([3000, 4000]);
        });

        it("snaps the subtitle's start/end time to the current time", function() {
            $scope.currentTime = 3400;
            $scope.duration = 5000;
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub3.div);
            expect(dragHandler.snappings.sort()).toEqual([-600, 400]);
        });

        it('selects the subtitle', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub3.div);
            expect($scope.selectSubtitle).toHaveBeenCalledWith(sub3.subtitle);
        });

        it("adds the moving class when the drag starts", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub1.div);
            expect(sub1.div.hasClass('moving')).toBeFalsy();
            dragHandler.onDrag(1);
            expect(sub1.div.hasClass('moving')).toBeTruthy();
        });

        it("removes the moving class when the drag ends", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub1.div);
            dragHandler.onEnd();
            expect(sub1.div.hasClass('moving')).toBeFalsy();
        });

        it("adds the moving class after a timeout", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub1.div);
            expect(sub1.div.hasClass('moving')).toBeFalsy();
            $timeout.flush();
            expect(sub1.div.hasClass('moving')).toBeTruthy();
        });

        it("cancels the timeout when the drag ends", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub1.div);
            dragHandler.onEnd();
            $timeout.flush();
            expect(sub1.div.hasClass('moving')).toBeFalsy();
        });
    });

    describe('SubtitleDragHandlerLeft', function() {
        it('adjusts start times', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerLeft, sub3.div);
            dragHandler.onDrag(-100);
            expect(sub3.subtitle.getTimings()).toEqual([2900, 4000]);

            dragHandler.onDrag(100);
            expect(sub3.subtitle.getTimings()).toEqual([3100, 4000]);
        });

        it("doesn't adjust start times before time=0", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerLeft, sub1.div);
            dragHandler.onDrag(-100);
            expect(sub1.subtitle.getTimings()).toEqual([0, 1000]);
        });

        it("doesn't adjust start times so much that the subtitle is shorter than MIN_DURATION", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerLeft, sub3.div);
            dragHandler.onDrag(1000);
            expect(sub3.subtitle.getTimings()).toEqual([3750, 4000]);
        });

        it("doesn't push past the previous subtitle start time", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerLeft, sub3.div);
            dragHandler.onDrag(-1001);
            expect(sub3.subtitle.getTimings()).toEqual([2000, 4000]);
        });

        it("snaps the subtitle's end time to the current time", function() {
            $scope.currentTime = 3400;
            createHandler(TimelineDrag.SubtitleDragHandlerLeft, sub3.div);
            expect(dragHandler.snappings).toEqual([400]);
        });

        it('selects the subtitle', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerLeft, sub2.div);
            expect($scope.selectSubtitle).toHaveBeenCalledWith(sub2.subtitle);
        });

        it('adds the adjusting class to the left handle', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerLeft, sub2.div);
            expect(sub2.handleLeft.hasClass('adjusting')).toBeTruthy();
        });

        it('removes the adjusting class when the drag ends', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerLeft, sub2.div);
            dragHandler.onEnd();
            expect(sub2.handleLeft.hasClass('adjusting')).toBeFalsy();
        });
    });

    describe('SubtitleDragHandlerRight', function() {
        it('adjusts end times', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerRight, sub2.div);
            dragHandler.onDrag(100);
            expect(sub2.subtitle.getTimings()).toEqual([1000, 2100]);

            dragHandler.onDrag(-100);
            expect(sub2.subtitle.getTimings()).toEqual([1000, 1900]);
        });

        it("doesn't adjust end times past scope.duration", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerRight, sub3.div);
            dragHandler.onDrag(100);
            expect(sub3.subtitle.getTimings()).toEqual([3000, 4000]);
        });

        it("doesn't adjust end times so much that the subtitle is shorter than MIN_DURATION", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerRight, sub3.div);
            dragHandler.onDrag(-1000);
            expect(sub3.subtitle.getTimings()).toEqual([3000, 3250]);
        });

        it("doesn't push past the next subtitle start time", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerRight, sub2.div);
            dragHandler.onDrag(1001);
            expect(sub2.subtitle.getTimings()).toEqual([1000, 3000]);
        });

        it("snaps the subtitle's end time to the current time", function() {
            $scope.currentTime = 3400;
            createHandler(TimelineDrag.SubtitleDragHandlerRight, sub3.div);
            expect(dragHandler.snappings).toEqual([-600]);
        });

        it('selects the subtitle', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerRight, sub2.div);
            expect($scope.selectSubtitle).toHaveBeenCalledWith(sub2.subtitle);
        });

        it('adds the adjusting class to the right handle', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerRight, sub2.div);
            expect(sub2.handleRight.hasClass('adjusting')).toBeTruthy();
        });

        it('removes the adjusting class when the drag ends', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerRight, sub2.div);
            dragHandler.onEnd();
            expect(sub2.handleRight.hasClass('adjusting')).toBeFalsy();
        });
    });

    describe('SubtitleDragHandlerDual', function() {
        it('adjusts both start and end times', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerDual, sub1.div);
            dragHandler.onDrag(100);
            expect(sub1.subtitle.getTimings()).toEqual([0, 1100]);
            expect(sub2.subtitle.getTimings()).toEqual([1100, 2000]);

            dragHandler.onDrag(-100);
            expect(sub1.subtitle.getTimings()).toEqual([0, 900]);
            expect(sub2.subtitle.getTimings()).toEqual([900, 2000]);
        });

        it("doesn't adjust end times so much that the subtitle is shorter than MIN_DURATION", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerDual, sub1.div);
            dragHandler.onDrag(-1000);
            expect(sub1.subtitle.getTimings()).toEqual([0, 250]);
            expect(sub2.subtitle.getTimings()).toEqual([250, 2000]);
        });

        it("doesn't adjust start times so much that the second subtitle is shorter than MIN_DURATION", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerDual, sub1.div);
            dragHandler.onDrag(1000);
            expect(sub1.subtitle.getTimings()).toEqual([0, 1750]);
            expect(sub2.subtitle.getTimings()).toEqual([1750, 2000]);
        });

        it("snaps the first subtitle's end time to the current time", function() {
            $scope.currentTime = 1400;
            createHandler(TimelineDrag.SubtitleDragHandlerDual, sub1.div);
            expect(dragHandler.snappings).toEqual([400]);
        });

        it('selects the both subtitles', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerDual, sub1.div);
            expect($scope.selectSubtitle).toHaveBeenCalledWith(sub1.subtitle, sub2.subtitle);
        });

        it('selects the only the first subtitle once the drag stops', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerDual, sub1.div);
            $scope.selectSubtitle.calls.reset();
            dragHandler.onEnd();
            expect($scope.selectSubtitle).toHaveBeenCalledWith(sub1.subtitle);
        });

        it("adds the adjusting class to the first subtitle's right handle", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerDual, sub2.div);
            expect(sub2.handleRight.hasClass('adjusting')).toBeTruthy();
        });

        it("adds the adjusting class to the second subtitle's left handle", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerDual, sub2.div);
            expect(sub3.handleLeft.hasClass('adjusting')).toBeTruthy();
        });

        it('removes the adjusting class when the drag ends', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerDual, sub2.div);
            dragHandler.onEnd();
            expect(sub2.handleRight.hasClass('adjusting')).toBeFalsy();
            expect(sub3.handleLeft.hasClass('adjusting')).toBeFalsy();
        });
    });

    describe('DragHandlerTimeline', function() {
        var timelineDragSpy;

        beforeEach(function() {
            timelineDragSpy = jasmine.createSpy('timelineDragSpy');
            $scope.redrawSubtitles = jasmine.createSpy('redrawSubtitles');
            $scope.currentTime = 1000;
            $scope.$on('timeline-drag', timelineDragSpy);
        });

        it("emits timeline-drag when the timeline is dragged", function() {
            createHandler(TimelineDrag.DragHandlerTimeline, null, 1500);
            dragHandler.onDrag(200);

            expect(timelineDragSpy).toHaveBeenCalledWith(jasmine.any(Object), -200);

            timelineDragSpy.calls.reset();
            dragHandler.onDrag(-100);
            expect(timelineDragSpy).toHaveBeenCalledWith(jasmine.any(Object), 100);

            // After mouse up it should stop dragging the timeline
            dragHandler.onDrag(-200);
            timelineDragSpy.calls.reset();
            expect(timelineDragSpy).not.toHaveBeenCalled();
        });

        it("calls redrawSubtitles when the timeline is dragged", function() {
            createHandler(TimelineDrag.DragHandlerTimeline, null, 1500);
            dragHandler.onDrag(200);
            expect($scope.redrawSubtitles).toHaveBeenCalledWith({ deltaMS: -200});
        });

        it("seeks the video when the mouse is released", function() {
            createHandler(TimelineDrag.DragHandlerTimeline, null, 1500);
            dragHandler.onDrag(200);
            dragHandler.onEnd();
            expect(VideoPlayer.seek).toHaveBeenCalledWith(800);
        });

        it("seeks to clickTime if no motion is deticted", function() {
            createHandler(TimelineDrag.DragHandlerTimeline, null, 1500);
            dragHandler.onEnd();
            expect(VideoPlayer.seek).toHaveBeenCalledWith(1500);
        });

        it("doesn't seek before time=0", function() {
            createHandler(TimelineDrag.DragHandlerTimeline, null, 1500);
            dragHandler.onDrag(1001);
            expect(timelineDragSpy).toHaveBeenCalledWith(jasmine.any(Object), -1000);
        });

        it("doesn't seek past duration", function() {
            createHandler(TimelineDrag.DragHandlerTimeline, null, 1500);
            dragHandler.onDrag(-3001);
            expect(timelineDragSpy).toHaveBeenCalledWith(jasmine.any(Object), 3000);
        });
    });

    describe('deltaPXToDeltaMS', function() {
        it("converts 1px to 10 ms", function() {
            expect(TimelineDrag.deltaPXToDeltaMS(1, $scope)).toEqual(10);
            expect(TimelineDrag.deltaPXToDeltaMS(10, $scope)).toEqual(100);
            expect(TimelineDrag.deltaPXToDeltaMS(-1, $scope)).toEqual(-10);
        });

        it("implements snapping", function() {
            expect(TimelineDrag.deltaPXToDeltaMS(12, $scope, [100])).toEqual(100);
            expect(TimelineDrag.deltaPXToDeltaMS(15, $scope, [100])).toEqual(100);
            expect(TimelineDrag.deltaPXToDeltaMS(5, $scope, [100])).toEqual(100);
            expect(TimelineDrag.deltaPXToDeltaMS(16, $scope, [100])).toEqual(160);
            expect(TimelineDrag.deltaPXToDeltaMS(4, $scope, [100])).toEqual(40);
        });
    });

});
