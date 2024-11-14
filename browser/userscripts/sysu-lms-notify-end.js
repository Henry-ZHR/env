// ==UserScript==
// @name        sysu lms notify end
// @match       https://lms.sysu.edu.cn/mod/fsresource/view.php*
// @grant       GM_notification
// @version     0
// @run-at      document-end
// @author      Henry-ZHR
// @description Notify user when videos end
// @downloadURL https://raw.githubusercontent.com/Henry-ZHR/env/refs/heads/master/browser/userscripts/sysu-lms-notify-end.js
// ==/UserScript==

(function () {
    "use strict";

    const TAG = "SYSU-LMS";

    setTimeout(function () {
        const player = document.getElementById("player-con");
        if (!player) {
            window.alert("Can't find player");
            return;
        }
        const video = player.querySelector("video");
        if (!video) {
            window.alert("Can't find video");
            return;
        }
        video.addEventListener("ended", (event) => {
            GM_notification(`[${TAG}] Video ended!`);
        })
        GM_notification(`[${TAG}] Added listener`);
    }, 1000)
})();