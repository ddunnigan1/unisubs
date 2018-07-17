describe('TimelineDrag', function() {
    var $scope;
    var $timeout;
    var subtitleList;
    var sub1, sub2, sub3;
    var VideoPlayer;
    var lastPageX;
    var TimelineDrag;
    var dragHandler;

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

    function createHandler(handlerClass, subtitleDiv, pageX) {
        dragHandler = new handlerClass($scope, pageX, subtitleDiv);
    }

    describe('SubtitleDragHandlerMiddle', function() {
        it('moves subtitles', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub2.div, 0);
            dragHandler.onDrag(20);
            expect(sub2.subtitle.getTimings()).toEqual([1200, 2200]);

            dragHandler.onDrag(10);
            expect(sub2.subtitle.getTimings()).toEqual([1100, 2100]);
        });

        it("uses a single changeGroup to allow undoing all changes at once", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub2.div, 0);
            dragHandler.onDrag(1);
            dragHandler.onDrag(2);
            dragHandler.onDrag(3);
            dragHandler.onEnd();
            subtitleList.undo();
            expect(sub2.subtitle.getTimings()).toEqual([1000, 2000]);
        });

        it("doesn't move subtitles over other subtitles timings", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub2.div, 0);
            dragHandler.onDrag(-1);
            expect(sub2.subtitle.getTimings()).toEqual([1000, 2000]);

            dragHandler.onDrag(101);
            expect(sub2.subtitle.getTimings()).toEqual([2000, 3000]);
        });

        it("doesn't move subtitles before time=0", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub1.div, 0);
            dragHandler.onDrag(-1);
            expect(sub1.subtitle.getTimings()).toEqual([0, 1000]);
        });

        it("doesn't move subtitles after time=scope.duration", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub3.div, 0);
            dragHandler.onDrag(1);
            expect(sub3.subtitle.getTimings()).toEqual([3000, 4000]);
        });

        it('selects the subtitle', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub3.div, 0);
            expect($scope.selectSubtitle).toHaveBeenCalledWith(sub3.subtitle);
        });

        it("adds the moving class when the drag starts", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub1.div, 0);
            expect(sub1.div.hasClass('moving')).toBeFalsy();
            dragHandler.onDrag(1);
            expect(sub1.div.hasClass('moving')).toBeTruthy();
        });

        it("removes the moving class when the drag ends", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub1.div, 0);
            dragHandler.onEnd();
            expect(sub1.div.hasClass('moving')).toBeFalsy();
        });

        it("adds the moving class after a timeout", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub1.div, 0);
            expect(sub1.div.hasClass('moving')).toBeFalsy();
            $timeout.flush();
            expect(sub1.div.hasClass('moving')).toBeTruthy();
        });

        it("cancels the timeout when the drag ends", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerMiddle, sub1.div, 0);
            dragHandler.onEnd();
            $timeout.flush();
            expect(sub1.div.hasClass('moving')).toBeFalsy();
        });
    });

    describe('SubtitleDragHandlerLeft', function() {
        it('adjusts start times', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerLeft, sub3.div, 0);
            dragHandler.onDrag(-10);
            expect(sub3.subtitle.getTimings()).toEqual([2900, 4000]);

            dragHandler.onDrag(10);
            expect(sub3.subtitle.getTimings()).toEqual([3100, 4000]);
        });

        it("doesn't adjust start times before time=0", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerLeft, sub1.div, 0);
            dragHandler.onDrag(-10);
            expect(sub1.subtitle.getTimings()).toEqual([0, 1000]);
        });

        it("doesn't adjust start times so much that the subtitle is shorter than MIN_DURATION", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerLeft, sub3.div, 0);
            dragHandler.onDrag(100);
            expect(sub3.subtitle.getTimings()).toEqual([3750, 4000]);
        });

        it("doesn't push past the previous subtitle start time", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerLeft, sub3.div, 0);
            dragHandler.onDrag(-101);
            expect(sub3.subtitle.getTimings()).toEqual([2000, 4000]);
        });

        it('selects the subtitle', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerLeft, sub2.div, 0);
            expect($scope.selectSubtitle).toHaveBeenCalledWith(sub2.subtitle);
        });
    });

    describe('SubtitleDragHandlerRight', function() {
        it('adjusts end times', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerRight, sub2.div, 0);
            dragHandler.onDrag(10);
            expect(sub2.subtitle.getTimings()).toEqual([1000, 2100]);

            dragHandler.onDrag(-10);
            expect(sub2.subtitle.getTimings()).toEqual([1000, 1900]);
        });

        it("doesn't adjust end times past scope.duration", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerRight, sub3.div, 0);
            dragHandler.onDrag(10);
            expect(sub3.subtitle.getTimings()).toEqual([3000, 4000]);
        });

        it("doesn't adjust end times so much that the subtitle is shorter than MIN_DURATION", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerRight, sub3.div, 0);
            dragHandler.onDrag(-100);
            expect(sub3.subtitle.getTimings()).toEqual([3000, 3250]);
        });

        it("doesn't push past the next subtitle start time", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerRight, sub2.div, 0);
            dragHandler.onDrag(101);
            expect(sub2.subtitle.getTimings()).toEqual([1000, 3000]);
        });

        it('selects the subtitle', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerRight, sub2.div, 0);
            expect($scope.selectSubtitle).toHaveBeenCalledWith(sub2.subtitle);
        });
    });

    describe('SubtitleDragHandlerDual', function() {
        it('adjusts both start and end times', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerDual, sub1.div, 0);
            dragHandler.onDrag(10);
            expect(sub1.subtitle.getTimings()).toEqual([0, 1100]);
            expect(sub2.subtitle.getTimings()).toEqual([1100, 2000]);

            dragHandler.onDrag(-10);
            expect(sub1.subtitle.getTimings()).toEqual([0, 900]);
            expect(sub2.subtitle.getTimings()).toEqual([900, 2000]);
        });

        it("doesn't adjust end times so much that the subtitle is shorter than MIN_DURATION", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerDual, sub1.div, 0);
            dragHandler.onDrag(-100);
            expect(sub1.subtitle.getTimings()).toEqual([0, 250]);
            expect(sub2.subtitle.getTimings()).toEqual([250, 2000]);
        });

        it("doesn't adjust start times so much that the second subtitle is shorter than MIN_DURATION", function() {
            createHandler(TimelineDrag.SubtitleDragHandlerDual, sub1.div, 0);
            dragHandler.onDrag(100);
            expect(sub1.subtitle.getTimings()).toEqual([0, 1750]);
            expect(sub2.subtitle.getTimings()).toEqual([1750, 2000]);
        });

        it('selects the both subtitles', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerDual, sub1.div, 0);
            expect($scope.selectSubtitle).toHaveBeenCalledWith(sub1.subtitle, sub2.subtitle);
        });

        it('selects the only the first subtitle once the drag stops', function() {
            createHandler(TimelineDrag.SubtitleDragHandlerDual, sub1.div, 0);
            $scope.selectSubtitle.calls.reset();
            dragHandler.onEnd();
            expect($scope.selectSubtitle).toHaveBeenCalledWith(sub1.subtitle);
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
            createHandler(TimelineDrag.DragHandlerTimeline, null, 0);
            dragHandler.onDrag(20);

            expect(timelineDragSpy).toHaveBeenCalledWith(jasmine.any(Object), -200);

            timelineDragSpy.calls.reset();
            dragHandler.onDrag(-10);
            expect(timelineDragSpy).toHaveBeenCalledWith(jasmine.any(Object), 100);

            // After mouse up it should stop dragging the timeline
            dragHandler.onDrag(-20);
            timelineDragSpy.calls.reset();
            expect(timelineDragSpy).not.toHaveBeenCalled();
        });

        it("calls redrawSubtitles when the timeline is dragged", function() {
            createHandler(TimelineDrag.DragHandlerTimeline, null, 0);
            dragHandler.onDrag(20);
            expect($scope.redrawSubtitles).toHaveBeenCalledWith({ deltaMS: -200});
        });

        it("seeks the video when the mouse is released", function() {
            createHandler(TimelineDrag.DragHandlerTimeline, null, 0);
            dragHandler.onDrag(20);
            dragHandler.onEnd();
            expect(VideoPlayer.seek).toHaveBeenCalledWith(800);
        });

        it("doesn't seek before time=0", function() {
            createHandler(TimelineDrag.DragHandlerTimeline, null, 0);
            dragHandler.onDrag(101);
            expect(timelineDragSpy).toHaveBeenCalledWith(jasmine.any(Object), -1000);
        });

        it("doesn't seek past duration", function() {
            createHandler(TimelineDrag.DragHandlerTimeline, null, 0);
            dragHandler.onDrag(-301);
            expect(timelineDragSpy).toHaveBeenCalledWith(jasmine.any(Object), 3000);
        });
    });

});
