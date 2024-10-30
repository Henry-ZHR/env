// ==UserScript==
// @name               中大自动验证码认证
// @name:en            SYSU CAS Auto Captcha Login
// @name:zh            中大自动验证码认证
// @namespace          https://github.com/KumaTea
// @namespace          https://greasyfork.org/en/users/169784-kumatea
// @homepage           https://github.com/KumaTea/SYSU-CAS
// @version            1.2.0.0
// @description        中山大学身份验证系统自动识别验证码登录
// @description:en     Automatic Script for Solving captcha of CAS (Central Authentication Service) of Sun Yat-sen University
// @description:zh     中山大学身份验证系统自动识别验证码登录
// @description:zh-cn  中山大学身份验证系统自动识别验证码登录
// @author             KumaTea
// @match              https://cas.sysu.edu.cn/cas/login*
// @match              https://cas-443.webvpn.sysu.edu.cn/cas/login*
// @license            GPLv3
// @require            https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js
// @run-at             document-end
// @downloadURL        https://raw.githubusercontent.com/Henry-ZHR/env/refs/heads/master/browser/userscripts/sysu-cas-captcha.js
// ==/UserScript==

(function () {
    'use strict';

    const { createWorker } = Tesseract;

    const captcha_rm_regex = /[^A-Za-z0-9]/g;
    const black_threshold = 50;


    function react_input(component, value) {
        // Credit: https://github.com/facebook/react/issues/11488#issuecomment-347775628
        let last_value = component.value;
        component.value = value;
        let event = new Event("input", { bubbles: true });
        // React 15
        event.simulated = true;
        // React 16
        let tracker = component._valueTracker;
        if (tracker) {
            tracker.setValue(last_value);
        }
        component.dispatchEvent(event);
    }


    function replace_color_in_canvas(canvas) {
        let ctx = canvas.getContext("2d");
        let imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        let data = imageData.data;
        let len = data.length / 3;
        let first_pixel_array = [data[0], data[1], data[2]];
        for (let i = 0; i < len; i += 1) {
            let r = data[i * 3];
            let g = data[i * 3 + 1];
            let b = data[i * 3 + 2];
            if (r + g < black_threshold || r + b < black_threshold || g + b < black_threshold) {
                data[i * 3] = first_pixel_array[0];
                data[i * 3 + 1] = first_pixel_array[1];
                data[i * 3 + 2] = first_pixel_array[2];
            }
        }
        ctx.putImageData(imageData, 0, 0);
        return ctx;
    }


    function img_src_to_base64(img) {
        // Ref: https://stackoverflow.com/a/22172860/10714490
        let canvas = document.createElement("canvas");
        canvas.width = img.width;
        canvas.height = img.height;
        let ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0);
        ctx = replace_color_in_canvas(ctx.canvas);
        return ctx.canvas.toDataURL("image/png");
    }


    function clone_image(img) {
        let new_img = document.createElement("img");
        new_img.src = img_src_to_base64(img)
        return new_img;
    }


    async function recognize() {
        const worker = await createWorker('eng', 1, {}, {
            psm: 7, // Treat the image as a single text line
            segment_penalty_dict_frequent_word: 1,
            segment_penalty_dict_case_ok: 1,
            segment_penalty_dict_case_bad: 1,
            segment_penalty_dict_nonword: 1,
            segment_penalty_garbage: 1,
        });
        let img = document.getElementById('captchaImg');
        await img.decode();
        let { data: { text } } = await worker.recognize(clone_image(img));
        return text.replace(captcha_rm_regex, "");
    }


    async function solve() {
        const captcha = document.getElementById("captcha");

        if (!captcha) {
            console.log("Could not find captcha");
            return;
        }

        captcha.placeholder = "Recognizing...";

        let result = await recognize();
        console.log("Result: " + result);
        react_input(captcha, result);

        if (result.length !== 4) {
            if (window.confirm("Captcha seems incorrect:" + result + "\nReload?")) {
                location.reload();
            }
        }

        // 准确度有点低，暂时不自动提交
        // document.querySelector("input.btn.btn-submit.btn-block").click();
    }


    solve();
})();