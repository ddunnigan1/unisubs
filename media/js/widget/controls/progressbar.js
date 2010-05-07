// Universal Subtitles, universalsubtitles.org
// 
// Copyright (C) 2010 Participatory Culture Foundation
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

goog.provide('mirosubs.controls.ProgressBar');

mirosubs.controls.ProgressBar = function(videoPlayer) {
    goog.ui.Component.call(this);
    this.videoPlayer_ = videoPlayer;
    this.videoDuration_ = 0;
};
goog.inherits(mirosubs.controls.ProgressBar, goog.ui.Component);

mirosubs.controls.ProgressBar.prototype.createDom = function() {
    mirosubs.controls.ProgressBar.superClass_.createDom.call(this);
    this.bufferedBar_ = new mirosubs.controls.BufferedBar(
        this.videoPlayer_);
    this.addChild(this.bufferedBar_);
    this.progressSlider_ = new mirosubs.controls.ProgressSlider();
    this.addChild(this.progressSlider_, true);
};

mirosubs.controls.ProgressBar.prototype.enterDocument = function() {
    mirosubs.controls.ProgressBar.superClass_.enterDocument.call(this);
    var et = mirosubs.AbstractVideoPlayer.EventType;
    this.getHandler().listen(
        this.videoPlayer_, et.TIMEUPDATE, this.videoTimeUpdate_);
};

mirosubs.controls.ProgressBar.prototype.videoTimeUpdate_ = function(event) {
    if (this.videoDuration_ == 0) {
        this.videoDuration_ = this.videoPlayer_.getDuration();
        if (this.videoDuration_ == 0)
            return;
    }
    // TODO: you're probably going to have to make sure user isn't currently
    // manipulating slider value.
    this.progressSlider_.setValue(
        100 * this.videoPlayer_.getPlayheadTime() / this.videoDuration_);
};