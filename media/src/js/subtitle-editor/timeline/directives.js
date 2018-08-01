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

var angular = angular || null;

(function() {
    var module = angular.module('amara.SubtitleEditor.timeline.directives', []);

    /*
     * Define a couple of helper classes to handle updating the timeline
     * elements.  Our basic strategy is to make a really wide div, so that we
     * have a bit of a buffer, then scroll the div instead of re-rendering
     * everything.
     */
    function durationToPixels(duration, scale) {
        // by default 1 pixel == 10 ms.  scope.scale can adjusts that,
        // although there isn't any interface for it.
        return Math.floor(scale * duration / 10);
    }

    function pixelsToDuration(width, scale) {
        return width * 10 / scale;
    }

    function BufferTimespan(scope) {
        /* Stores the time range of the entire div.*/
        this.duration = 60000; // Buffer 1 minute of subtitles.
        // Position the buffer so that most of it is in front of the current
        // time.
        if(scope.currentTime !== null) {
            var currentTime = scope.currentTime;
        } else {
            var currentTime = 0;
        }
        this.startTime = currentTime - this.duration / 4;
        // We don't want to buffer negative times, but do let startTime go to
        // -0.5 seconds because the left side of the "0" is slightly left of
        // time=0.
        if(this.startTime < -500) {
            this.startTime = -500;
        }
        this.endTime = this.startTime + this.duration;
        if(scope.duration !== null) {
            this.endTime = Math.min(this.endTime, scope.duration)
        }
        this.width = durationToPixels(this.duration, scope.scale);
    }

    function VisibleTimespan(scope, width, deltaMS) {
        /* Stores the portion of the video time that is displayed in the
         * timeline.
         */

        this.scope = scope;
        this.scale = scope.scale;
        this.duration = pixelsToDuration(width, this.scale);
        if(scope.currentTime !== null) {
            var currentTime = scope.currentTime;
        } else {
            var currentTime = 0;
        }
        this.startTime = currentTime - this.duration / 2;
        if(deltaMS) {
            this.startTime += deltaMS;
        }
        this.endTime = this.startTime + this.duration;
    }

    VisibleTimespan.prototype.fitsInBuffer = function(bufferTimespan) {
        if(this.startTime < bufferTimespan.startTime && bufferTimespan.startTime > 0) {
            return false;
        }
        if(this.endTime > bufferTimespan.endTime && bufferTimespan.endTime < this.scope.duration) {
            return false;
        }
        return true;
    }

    VisibleTimespan.prototype.positionDiv = function(bufferTimespan, div) {
        var deltaTime = this.startTime - bufferTimespan.startTime;
        div.css('left', -durationToPixels(deltaTime, this.scale) + 'px');
    }

    VisibleTimespan.prototype.isSubtitleVisible = function(subtitle) {
        return this.startTime < subtitle.startTime && this.endTime > subtitle.endTime;
    }

    // Handle the DnD from the timeline
    //
    // We define separate classes to handle the different ways of dragging -- moving subtitles, adjusting start/end times, dragging the timeline, etc.
    module.service('TimelineDrag', ['MIN_DURATION', '$timeout', '$document', 'VideoPlayer', function(MIN_DURATION, $timeout, $document, VideoPlayer) {
        $document = $($document); // Ensure we're using jQuery, not jQuery lite
        var changeGroupCounter = 1;

        // Base class for drag handlers
        function DragHandler($scope, subtitleDiv, clickTime) {
            this.$scope = $scope;
            this.subtitleDiv = subtitleDiv;
            this.clickTime = clickTime;
            this.subtitleList = this.$scope.workingSubtitles.subtitleList;
            this.changeGroup = 'timeline-drag-' + changeGroupCounter++;
            this.minDeltaMS = -Number.MAX_SAFE_INTEGER;
            this.maxDeltaMS = Number.MAX_SAFE_INTEGER;
            this.snappings = []; // deltaMS values that we gravitate to when adjusting things with the mouse
        }

        DragHandler.prototype = {
            clampDeltaMS: function(deltaMS) {
                return Math.min(Math.max(deltaMS, this.minDeltaMS), this.maxDeltaMS);
            },
            // These are implemented by subclasses
            onDrag: function(deltaMS) {}, // handle the user moving the mouse with the button held down
            onEnd: function() {} // Handle the user releasing the mouse or leaving the window
        }

        // Handler for dragging the timeline
        //
        // While the user is dragging, we move the timeline in the direction of
        // the drag.  Once the user releases the mouse button, we seek the
        // video
        //
        //
        function DragHandlerTimeline($scope, subtitleDiv, clickTime) {
            DragHandler.call(this, $scope, subtitleDiv, clickTime);
            this.minDeltaMS = -this.$scope.currentTime;
            this.maxDeltaMS = this.$scope.duration - this.$scope.currentTime;
            this.lastDeltaMS = 0;
            this.sawDrag = false;
        }

        _.extend(DragHandlerTimeline.prototype, DragHandler.prototype, {
            onDrag: function(deltaMS) {
                // Since we're dragging the timeline, moving right seeks
                // backwards and moving left seeks forward.
                deltaMS = -deltaMS;

                var deltaMS = this.clampDeltaMS(deltaMS);
                this.$scope.$emit('timeline-drag', deltaMS);
                this.$scope.redrawSubtitles({ deltaMS: deltaMS });
                this.lastDeltaMS = deltaMS;
                this.sawDrag = true;
            },
            onEnd: function() {
                if(!this.sawDrag) {
                    VideoPlayer.seek(this.clickTime);
                }  else if(this.$scope.currentTime !== null) {
                    VideoPlayer.seek(this.$scope.currentTime + this.lastDeltaMS);
                }
            },
        });

        // Base class for dragging subtitles
        function SubtitleDragHandler($scope, subtitleDiv, clickTime) {
            DragHandler.call(this, $scope, subtitleDiv, clickTime);
            this.calcSubtitlesInvolved();
            this.calcInitialTimings();
            this.calcDragDoundaries();
            this.calcSnappings();
            this.selectSubtitle();
        }

        _.extend(SubtitleDragHandler.prototype, DragHandler.prototype, {
            calcDragDoundaries: function() {},
            calcSnappings: function() {},
            calcSubtitlesInvolved: function() {
                this.draggingSubtitle = this.subtitleDiv.data('subtitle');
                this.nextSubtitle = this.subtitleList.nextSubtitle(this.draggingSubtitle);
                this.prevSubtitle = this.subtitleList.prevSubtitle(this.draggingSubtitle);
                if(this.nextSubtitle && !this.nextSubtitle.isSynced()) {
                    this.nextSubtitle = null;
                }
                if(this.prevSubtitle && !this.prevSubtitle.isSynced()) {
                    this.prevSubtitle = null;
                }
            },
            calcInitialTimings: function () {
                this.initialStartTime = this.draggingSubtitle.startTime;
                this.initialEndTime = this.draggingSubtitle.endTime;
                this.initialNextStartTime = this.nextSubtitle ? this.nextSubtitle.startTime : null;
                this.initialPrevEndTime = this.prevSubtitle ? this.prevSubtitle.endTime : null;
            },
            updateSubtitleTimes: function(changes) {
                this.subtitleList.updateSubtitleTimes(changes, this.changeGroup);
                this.$scope.$root.$emit("work-done");
            },
            selectSubtitle: function() {
                this.$scope.selectSubtitle(this.draggingSubtitle);
            }
        });

        // Handle dragging the subtitle from the middle -- this moves the subtitle in the timeline
        function SubtitleDragHandlerMiddle($scope, subtitleDiv, clickTime) {
            SubtitleDragHandler.call(this, $scope, subtitleDiv, clickTime);
            this.timeout = $timeout(function() { subtitleDiv.addClass('moving'); }, 100);
        }

        _.extend(SubtitleDragHandlerMiddle.prototype, SubtitleDragHandler.prototype, {
            calcDragDoundaries: function() {
                this.minDeltaMS = -this.draggingSubtitle.startTime;
                if(this.prevSubtitle) {
                    this.minDeltaMS = Math.max(this.minDeltaMS, -(this.draggingSubtitle.startTime - this.prevSubtitle.endTime));
                }

                this.maxDeltaMS = this.$scope.duration - this.draggingSubtitle.endTime;
                if(this.nextSubtitle) {
                    this.maxDeltaMS = Math.min(this.maxDeltaMS, this.nextSubtitle.startTime - this.draggingSubtitle.endTime);
                }
            },
            calcSnappings: function() {
                this.snappings = [
                    this.$scope.currentTime - this.draggingSubtitle.endTime,
                    this.$scope.currentTime - this.draggingSubtitle.startTime,
                ];
            },
            onDrag: function(deltaMS) {
                var deltaMS = this.clampDeltaMS(deltaMS);
                var changes = [
                    {
                        subtitle: this.draggingSubtitle,
                        startTime: this.initialStartTime + deltaMS,
                        endTime: this.initialEndTime + deltaMS,
                    }
                ];

                this.updateSubtitleTimes(changes);
                this.subtitleDiv.addClass('moving');
            },
            onEnd: function() {
                this.subtitleDiv.removeClass('moving');
                $timeout.cancel(this.timeout);
            }
        });

        // Handle dragging the subtitle by the left handle -- this adjusts the start time
        //
        // If the user drags it far enough back to hit the previous subtitle, then it also adjusts that subtitle's end time
        function SubtitleDragHandlerLeft($scope, subtitleDiv, clickTime) {
            SubtitleDragHandler.call(this, $scope, subtitleDiv, clickTime);
            $('.handle.left', subtitleDiv).addClass('adjusting');
        }

        _.extend(SubtitleDragHandlerLeft.prototype, SubtitleDragHandler.prototype, {
            calcDragDoundaries: function() {
                this.minDeltaMS = -this.draggingSubtitle.startTime;
                this.maxDeltaMS = this.draggingSubtitle.duration() - MIN_DURATION;

                if(this.prevSubtitle) {
                    this.minDeltaMS = Math.max(this.minDeltaMS, -(this.draggingSubtitle.startTime - this.prevSubtitle.endTime));
                }
            },
            calcSnappings: function() {
                this.snappings = [this.$scope.currentTime - this.draggingSubtitle.startTime];
            },
            onDrag: function(deltaMS) {
                var deltaMS = this.clampDeltaMS(deltaMS);
                var newStartTime = this.initialStartTime + deltaMS;
                var changes = [
                    {
                        subtitle: this.draggingSubtitle,
                        startTime: newStartTime,
                        endTime: this.draggingSubtitle.endTime,
                    }
                ];

                this.updateSubtitleTimes(changes);
            },
            onEnd: function() {
                $('.handle.left', this.subtitleDiv).removeClass('adjusting');
            }
        });

        // Handle dragging the subtitle by the right handle -- this adjusts the end time
        //
        // If the user drags it far enough forward to hit the next subtitle, then it also adjusts that subtitle's start time
        function SubtitleDragHandlerRight($scope, subtitleDiv, clickTime) {
            SubtitleDragHandler.call(this, $scope, subtitleDiv, clickTime);
            $('.handle.right', this.subtitleDiv).addClass('adjusting');
        }

        _.extend(SubtitleDragHandlerRight.prototype, SubtitleDragHandler.prototype, {
            calcDragDoundaries: function() {
                this.minDeltaMS = -(this.draggingSubtitle.duration() - MIN_DURATION);
                this.maxDeltaMS = this.$scope.duration - this.draggingSubtitle.endTime;

                if(this.nextSubtitle) {
                    this.maxDeltaMS = Math.min(this.maxDeltaMS, this.nextSubtitle.startTime - this.draggingSubtitle.endTime);
                }
            },
            calcSnappings: function() {
                this.snappings = [this.$scope.currentTime - this.draggingSubtitle.endTime];
            },
            onDrag: function(deltaMS) {
                var deltaMS = this.clampDeltaMS(deltaMS);
                var newEndTime = this.initialEndTime + deltaMS;
                var changes = [
                    {
                        subtitle: this.draggingSubtitle,
                        startTime: this.draggingSubtitle.startTime,
                        endTime: newEndTime
                    }
                ];

                this.updateSubtitleTimes(changes);
            },
            onEnd: function() {
                $('.handle.right', this.subtitleDiv).removeClass('adjusting');
            }
        });

        // Handle dragging the subtitle by the "dual" handle -- this adjusts both the end time of this sub, and the start time of the next
        //
        function SubtitleDragHandlerDual($scope, subtitleDiv, clickTime) {
            SubtitleDragHandler.call(this, $scope, subtitleDiv, clickTime);
            this.handles = $('.handle.right', this.subtitleDiv).add($('.handle.left', this.subtitleDiv.next()));
            this.handles.addClass('adjusting');
        }

        _.extend(SubtitleDragHandlerDual.prototype, SubtitleDragHandler.prototype, {
            calcDragDoundaries: function() {
                this.minDeltaMS = -(this.draggingSubtitle.duration() - MIN_DURATION);
                this.maxDeltaMS = this.$scope.duration - this.draggingSubtitle.endTime;
                this.maxDeltaMS = Math.min(this.maxDeltaMS, this.nextSubtitle.endTime - this.draggingSubtitle.endTime - MIN_DURATION);
            },
            calcSnappings: function() {
                this.snappings = [this.$scope.currentTime - this.draggingSubtitle.endTime];
            },
            onDrag: function(deltaMS) {
                var deltaMS = this.clampDeltaMS(deltaMS);
                var newEndTime = this.initialEndTime + deltaMS;
                var changes = [
                    {
                        subtitle: this.draggingSubtitle,
                        startTime: this.draggingSubtitle.startTime,
                        endTime: newEndTime
                    },
                    {
                        subtitle: this.nextSubtitle,
                        startTime: newEndTime,
                        endTime: this.nextSubtitle.endTime,
                    }
                ];

                this.updateSubtitleTimes(changes);
            },
            onEnd: function() {
                this.$scope.selectSubtitle(this.draggingSubtitle);
                this.handles.removeClass('adjusting');
            },
            selectSubtitle: function() {
                this.$scope.selectSubtitle(this.draggingSubtitle, this.nextSubtitle);
            }
        });

        // convert mouse movement in px to a deltaMS value that we can pass to onDrag
        function deltaPXToDeltaMS(deltaPX, $scope, deltaMSSnappings) {
            if(deltaMSSnappings) {
                for(var i=0; i < deltaMSSnappings.length; i++) {
                    var snapTo = deltaMSSnappings[i];

                    if(Math.abs(durationToPixels(snapTo, $scope.scale) - deltaPX) <= 5) {
                        return snapTo;
                    }
                }
            }
            return pixelsToDuration(deltaPX, $scope.scale);
        }

        function handleDragAndDrop($scope, subtitlesContainer) {
            function createDragHandler(evt, options) {
                if(options === undefined) {
                    options = {};
                }
                var target = $(evt.target);
                var subtitleDiv = target.closest('.subtitle', subtitlesContainer);
                var clickTime = calcClickTime(evt);

                if(subtitleDiv.length == 0) {
                    if(options.allowTimelineDrag === false) {
                        return null;
                    }
                    return new DragHandlerTimeline($scope, null, clickTime);
                }
                if(target.hasClass('handle')) {
                    if(target.hasClass('dual')) {
                        if(target.hasClass('left')) {
                            // Ensure that subtitleDiv is for first subtitle
                            subtitleDiv = subtitleDiv.prev();
                        }
                        return new SubtitleDragHandlerDual($scope, subtitleDiv);
                    } else if(target.hasClass('right')) {
                        return new SubtitleDragHandlerRight($scope, subtitleDiv);
                    } else if(target.hasClass('left')) {
                        return new SubtitleDragHandlerLeft($scope, subtitleDiv);
                    }
                }
                return new SubtitleDragHandlerMiddle($scope, subtitleDiv);
            }

            function calcClickTime(evt) {
                // FIXME: Would it be cleaner to just create a single BufferTimespan and VisibleTimespan?
                var bufferTimespan = new BufferTimespan($scope);
                return (bufferTimespan.startTime +
                        pixelsToDuration(evt.pageX - subtitlesContainer.offset().left, $scope.scale));
            }

            var dragHandler, initialPageX, initialTimestamp, sawMouseMove;
            var keyboardDragHandler, keyboardDeltaMS;

            subtitlesContainer.on('mousedown', function(evt) {
                if (evt.which == 3) {
                    return; // don't handle right-clicks
                }
                if($scope.duration === null || $scope.currentTime === null) {
                    // Don't know the duration yet, don't allow dragging
                    return;
                }

                stopKeyboardDrag();
                dragHandler = createDragHandler(evt);
                initialPageX = evt.pageX;
                initialTimestamp = evt.timeStamp;
                sawMouseMove = false;

                $document.on('mousemove.timelinedrag', function(evt) {
                    sawMouseMove = true;
                    var deltaMS = deltaPXToDeltaMS(evt.pageX - initialPageX, $scope, dragHandler.snappings);
                    dragHandler.onDrag(deltaMS);
                    $scope.$root.$digest();
                });
                $document.on('mouseup.timelinedrag', handleDragEnd);
                $document.on('mouseleave.timelinedrag', handleDragEnd);

                evt.stopPropagation();
                evt.preventDefault();
            });

            function handleDragEnd(evt) {
                $document.off('.timelinedrag');
                var oldDragHandler = dragHandler;
                dragHandler.onEnd();
                dragHandler = null;

                if(!sawMouseMove && (evt.timeStamp - initialTimestamp < 250)) {
                    startKeyboardDrag(evt);
                }
            }


            function startKeyboardDrag(evt) {
                keyboardDragHandler = createDragHandler(evt, { allowTimelineDrag: false});
                if(keyboardDragHandler === null) {
                    return;
                }
                keyboardDeltaMS = 0;
                // Stop the "drag" on any click.  Use addEventListener because
                // we want to get the event in the capture phase, before other
                // code has a chance to handle the event
                window.addEventListener('mousedown', stopKeyboardDrag, true);
            }

            function stopKeyboardDrag() {
                if(keyboardDragHandler) {
                    keyboardDragHandler.onEnd();
                    keyboardDragHandler = null;
                }
                window.removeEventListener('mousedown', stopKeyboardDrag, true);
            }

            $scope.$root.$on('key-down', function(evt, keyEvent) {
                if(keyboardDragHandler) {
                    if(keyEvent.keyCode == 37) {
                        keyboardDeltaMS -= keyEvent.shiftKey ? 10 : 100;
                        keyboardDragHandler.onDrag(keyboardDeltaMS);
                        evt.preventDefault();
                    } else if(keyEvent.keyCode == 39) {
                        keyboardDeltaMS += keyEvent.shiftKey ? 10 : 100;
                        keyboardDragHandler.onDrag(keyboardDeltaMS);
                        evt.preventDefault();
                    } else if(keyEvent.keyCode == 27) {
                        stopKeyboardDrag();
                        evt.preventDefault();
                    }
                }
            });
        }

        return {
            DragHandlerTimeline: DragHandlerTimeline,
            SubtitleDragHandlerLeft: SubtitleDragHandlerLeft,
            SubtitleDragHandlerMiddle: SubtitleDragHandlerMiddle,
            SubtitleDragHandlerRight: SubtitleDragHandlerRight,
            SubtitleDragHandlerDual: SubtitleDragHandlerDual,
            deltaPXToDeltaMS: deltaPXToDeltaMS,
            handleDragAndDrop: handleDragAndDrop
        }

    }]);

    module.directive('timelineTiming', ["displayTimeSecondsFilter", function(displayTimeSecondsFilter) {
        return function link(scope, elem, attrs) {
            var canvas = $(elem);
            var canvasElt = elem[0];
            var container = canvas.parent();
            var width=0, height=65; // dimensions of the canvas
            var containerWidth = container.width();
            var bufferTimespan = null;
            var visibleTimespan = null;

            function drawSecond(ctx, xPos, t) {
                // draw the second text on the timeline
                ctx.fillStyle = '#686868';
                var text = displayTimeSecondsFilter(t);
                var metrics = ctx.measureText(text);
                var x = xPos - (metrics.width / 2);
                ctx.fillText(text, x, 60);
            }
            function drawTics(ctx, xPos, duration) {
                // draw the tic marks between seconds
                // duration represents the amount of time to draw tics for in ms
                ctx.strokeStyle = '#686868';
                var divisions = duration / 250;
                var step = durationToPixels(250, scope.scale);
                ctx.lineWidth = 1;
                ctx.beginPath();
                for(var i = 1; i < divisions; i++) {
                    var x = Math.floor(0.5 + xPos + step * i);
                    x += 0.5;
                    ctx.moveTo(x, 60);
                    if(i == 2) {
                        // draw an extra long tic for the 50% mark;
                        ctx.lineTo(x, 45);
                    } else {
                        ctx.lineTo(x, 50);
                    }
                }
                ctx.stroke();
            }
            function drawCanvas() {
                var ctx = canvasElt.getContext("2d");
                ctx.clearRect(0, 0, width, height);
                ctx.font = (height / 5) + 'px Open Sans';

                var startTime = bufferTimespan.startTime;
                var endTime = bufferTimespan.endTime;
                if(startTime < 0) {
                    startTime = 0;
                }
                if(scope.duration) {
                    endTime = Math.min(endTime, scope.duration);
                }

                for(var t = startTime; t < endTime; t += 1000) {
                    var xPos = durationToPixels(t - bufferTimespan.startTime,
                            scope.scale);
                    drawSecond(ctx, xPos, t);
                    drawTics(ctx, xPos, Math.min(1000, endTime-t));
                }
            }

            function makeNewBuffer() {
                bufferTimespan = new BufferTimespan(scope);
                if(bufferTimespan.width != width) {
                    // Resize the width of the canvas to match the buffer
                    width = bufferTimespan.width;
                    canvasElt.width = width;
                    canvas.css('width', width + 'px');
                }
                drawCanvas();
            }

            // Put redrawCanvas in the scope, so that the controller can call
            // it.
            scope.redrawCanvas = function(deltaMS) {
                visibleTimespan = new VisibleTimespan(scope, containerWidth,
                        deltaMS);
                if(bufferTimespan === null ||
                    !visibleTimespan.fitsInBuffer(bufferTimespan) ||
                    bufferTimespan.endTime > scope.duration) {
                    makeNewBuffer();
                }
                visibleTimespan.positionDiv(bufferTimespan, canvas);
            };
            $(window).resize(function() {
                containerWidth = (container.width() || container.parent().width());
                scope.redrawCanvas();
            });
            scope.$on('timeline-drag', function(evt, deltaMS) {
                scope.redrawCanvas(deltaMS);
            });

            // Okay, finally done defining functions, let's draw the canvas.
            scope.redrawCanvas();
        }
    }]);

    module.directive('timelineSubtitles', ["VideoPlayer", "TimelineDrag", "MIN_DURATION", "DEFAULT_DURATION", function(VideoPlayer, TimelineDrag, MIN_DURATION, DEFAULT_DURATION) {
        return function link(scope, elem, attrs) {
            var timelineDiv = $(elem);
            var container = timelineDiv.parent();
            var containerWidth = container.width();
            var timelineDivWidth = 0;
            var bufferTimespan = null;
            var visibleTimespan = null;
            var contextMenu = $('#' + elem.data('context-menu'));
            var dragCounter = 0; // increments 1 for each drag we do.  Used to create unique changeGroups for updateSubtitleTimes
            // Map XML subtitle nodes to the div we created to show them
            var timelineDivs = {}
            // Store the DIV for the unsynced subtitle
            var unsyncedDiv = null;
            var unsyncedSubtitle = null;

            TimelineDrag.handleDragAndDrop(scope, elem);

            function subtitleList() {
                return scope.workingSubtitles.subtitleList;
            }

            function makeDivForSubtitle(subtitle) {
                var div = $('<div/>', {class: 'subtitle'});
                div.data('subtitle', subtitle);
                div.append($('<a href="#" class="handle left"></a>'));
                div.append($('<span/>', {class: 'timeline-subtitle-text'}));
                div.append($('<a href="#" class="handle right"></a>'));
                updateDivForSubtitle(div, subtitle);
                timelineDiv.append(div);
                return div;
            }

            function updateDivForSubtitle(div, subtitle) {
                $('span', div).html(subtitle.content());
                if(subtitle === scope.selectedSubtitle || subtitle.isDraftFor(scope.selectedSubtitle)) {
                    div.addClass('selected-subtitle');
                } else {
                    div.removeClass('selected-subtitle');
                }
                if(subtitle.isSynced()) {
                    div.removeClass('unsynced');
                }

                // See if we should create a dual handles -- one that adjusts the end time of this subtitle and the start time of the next at simultaniously.
                if(shouldCreateDualHandleLeft(subtitle)) {
                    if($('.handle.dual.left', div).length == 0) {
                        div.append($('<a href="#" class="handle dual left"></a>'));
                    }
                } else {
                    $('.handle.dual.left', div).remove();
                }
                if(shouldCreateDualHandleRight(subtitle)) {
                    if($('.handle.dual.right', div).length == 0) {
                        div.append($('<a href="#" class="handle dual right"></a>'));
                    }
                } else {
                    $('.handle.dual.right', div).remove();
                }
            }

            function shouldCreateDualHandleRight(subtitle) {
                if(subtitle.isSynced()) {
                    var nextSubtitle = subtitleList().nextSubtitle(subtitle);
                    if(nextSubtitle && nextSubtitle.isSynced() && nextSubtitle.startTime == subtitle.endTime) {
                        return true;
                    }
                }
                return false;
            }

            function shouldCreateDualHandleLeft(subtitle) {
                if(subtitle.isSynced()) {
                    var prevSubtitle = subtitleList().prevSubtitle(subtitle);
                    if(prevSubtitle && prevSubtitle.isSynced() && prevSubtitle.endTime == subtitle.startTime) {
                        return true;
                    }
                }
                return false;
            }

            function handleMouseDownInContainer(evt) {
                if (evt.which == 3) {
                    showContextMenu(evt);
                }
            }

            function placeSubtitle(startTime, endTime, div) {
                var x = durationToPixels(startTime - bufferTimespan.startTime,
                        scope.scale);
                var width = durationToPixels(endTime - startTime,
                        scope.scale);
                div.css({left: x, width: width});
            }

            function updateUnsyncedSubtitle() {
                /* Sometimes we want to show the first unsynced subtitle for
                 * the timeline.
                 *
                 * This method calculates if we want to show the subtitle or
                 * not and sets the unsyncedSubtitle variable accordingly.  If
                 * we don't want to show it, we set it to none.  If we do, we
                 * set it to a DraftSubtitle with the start/end times set
                 * based on the current time.
                 */
                var lastSynced = subtitleList().lastSyncedSubtitle();
                if(lastSynced !== null &&
                    lastSynced.endTime > scope.currentTime) {
                    // Not past the end of the synced subtitles
                    unsyncedSubtitle = null;
                    return;
                }
                var unsynced = subtitleList().firstUnsyncedSubtitle();
                if(unsynced === null) {
                    // All subtitles are synced.
                    unsyncedSubtitle = null;
                    return;
                }
                if(unsynced.startTime >= 0 && unsynced.startTime >
                        bufferTimespan.endTime) {
                    // unsynced subtitle has its start time set, and it's past
                    // the end of the timeline.
                    unsyncedSubtitle = null;
                    return;
                }


                if(unsyncedSubtitle === null) {
                    unsyncedSubtitle = unsynced.draftSubtitle();
                } else if (unsyncedSubtitle.storedSubtitle.id != unsynced.id) {
                    // We need to keep the stored subtitle up to date as
                    // it is used in the video overlay
                    unsyncedSubtitle = unsynced.draftSubtitle();
                }
                unsyncedSubtitle.markdown = unsynced.markdown;
                if(unsynced.startTime < 0) {
                    unsyncedSubtitle.startTime = scope.currentTime;
                    if(unsyncedSubtitle.startTime === null) {
                        // currentTime hasn't been set yet.  Let's use time=0
                        // for now.
                        unsyncedSubtitle.startTime = 0;
                    }
                    unsyncedSubtitle.endTime = scope.currentTime + DEFAULT_DURATION;
                } else {
                    unsyncedSubtitle.startTime = unsynced.startTime;
                    unsyncedSubtitle.endTime = Math.max(scope.currentTime,
                            unsynced.startTime + MIN_DURATION);
                }
            }

            function checkShownSubtitle() {
                // First check if the current subtitle is still shown, this is
                // the most common case, and it's fast
                if(scope.subtitle !== null &&
                    scope.subtitle.isAt(scope.currentTime)) {
                    return;
                }

                var shownSubtitle = subtitleList().subtitleAt(
                    scope.currentTime);
                if(shownSubtitle === null && unsyncedSubtitle !== null &&
                        unsyncedSubtitle.startTime <= scope.currentTime) {
                    shownSubtitle = unsyncedSubtitle.storedSubtitle;
                }
                scope.subtitle = shownSubtitle;
                if(shownSubtitle !== scope.timeline.shownSubtitle) {
                    scope.timeline.shownSubtitle = shownSubtitle;
                    var phase = scope.$root.$$phase;
                    if(phase != '$apply' && phase != '$digest') {
                        scope.$root.$digest();
                    }
                }
            }

            function placeSubtitles() {
                if(!scope.workingSubtitles) {
                    return;
                }
                var subtitles = subtitleList().getSubtitlesForTime(
                        bufferTimespan.startTime, bufferTimespan.endTime);
                var oldTimelineDivs = timelineDivs;
                timelineDivs = {}

                for(var i = 0; i < subtitles.length; i++) {
                    var subtitle = subtitles[i];
                    if(oldTimelineDivs.hasOwnProperty(subtitle.id)) {
                        var div = oldTimelineDivs[subtitle.id];
                        timelineDivs[subtitle.id] = div;
                        updateDivForSubtitle(div, subtitle);
                        delete oldTimelineDivs[subtitle.id];
                    } else {
                        var div = makeDivForSubtitle(subtitle);
                        timelineDivs[subtitle.id] = div;
                    }
                    placeSubtitle(subtitle.startTime, subtitle.endTime,
                            timelineDivs[subtitle.id]);
                }
                // remove divs no longer in the timeline
                for(var subId in oldTimelineDivs) {
                    oldTimelineDivs[subId].remove();
                }
            }
            function placeUnsyncedSubtitle() {
                updateUnsyncedSubtitle();
                if(unsyncedSubtitle !== null) {
                    if(unsyncedDiv === null) {
                        unsyncedDiv = makeDivForSubtitle(unsyncedSubtitle);
                        unsyncedDiv.addClass('unsynced');
                    } else {
                        updateDivForSubtitle(unsyncedDiv, unsyncedSubtitle);
                    }
                    placeSubtitle(unsyncedSubtitle.startTime,
                            unsyncedSubtitle.endTime, unsyncedDiv);
                } else if(unsyncedDiv !== null) {
                    unsyncedDiv.remove();
                    unsyncedDiv = null;
                }
            }
            function updateSubtitle(subtitle) {
                if(!subtitle) {
                    return;
                }
                if(timelineDivs.hasOwnProperty(subtitle.id)) {
                    updateDivForSubtitle(timelineDivs[subtitle.id], subtitle);
                } else if(unsyncedSubtitle && unsyncedSubtitle.isDraftFor(subtitle)) {
                    updateDivForSubtitle(unsyncedDiv, subtitle);
                }
            }

            // Put redrawSubtitles in the scope so that the controller can
            // call it.
            scope.redrawSubtitles = function(options) {
                if(options === undefined) {
                    options = {};
                }
                visibleTimespan = new VisibleTimespan(scope, containerWidth,
                        options.deltaMS);
                if(bufferTimespan === null ||
                    !visibleTimespan.fitsInBuffer(bufferTimespan)) {
                        bufferTimespan = new BufferTimespan(scope);
                    if(bufferTimespan.width != timelineDivWidth) {
                        timelineDivWidth = bufferTimespan.width;
                        timelineDiv.css('width', bufferTimespan.width + 'px');
                    }
                    placeSubtitles();
                } else if(options.forcePlace) {
                    placeSubtitles();
                }
                // always need to place the unsynced subtitle, since it
                // changes with the current time.
                placeUnsyncedSubtitle();
                checkShownSubtitle();

                visibleTimespan.positionDiv(bufferTimespan, timelineDiv);
            };

            container.on('mousedown', handleMouseDownInContainer);
            // Redraw the subtitles on window resize
            $(window).resize(function() {
                containerWidth = (container.width() || container.parent().width());
                scope.redrawSubtitles();
            });
            // Redraw them now as well
            scope.redrawSubtitles();

            scope.$watch('selectedSubtitle', function(selectedSubtitle, oldSelectedSubtitle) {
                updateSubtitle(oldSelectedSubtitle);
                updateSubtitle(selectedSubtitle);
                if(selectedSubtitle && selectedSubtitle.isSynced() && !visibleTimespan.isSubtitleVisible(selectedSubtitle)) {
                    VideoPlayer.seek(selectedSubtitle.startTime);
                }
            });

            function showContextMenu(evt) {
                contextMenu.show();
                contextMenu.css({"left": evt.clientX, "top": evt.clientY});
                // Use addEventListener because we want to hook up the handler in the capture phase -- before any other handler handles it.
                window.addEventListener('click', hideContextMenu, true);
            }

            function hideContextMenu(evt) {
                contextMenu.hide();
                window.removeEventListener('click', hideContextMenu, true);
            }
        }
    }]);
})();
