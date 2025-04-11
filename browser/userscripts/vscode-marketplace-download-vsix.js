// ==UserScript==
// @name        [VSCode Marketplace] Download VSIX
// @match       https://marketplace.visualstudio.com/items*
// @grant       none
// @version     0
// @author      Mirza Iqbal & Henry-ZHR
// @run-at      document-end
// ==/UserScript==

// from https://github.com/mjmirza/Download-VSIX-From-Visual-Studio-Market-Place/blob/main/downloadVSIX-V2.js
(function () {
    // Object to store extension data (version, identifier)
    const extensionData = {
        version: "",
        identifier: "",
        // Function to get the download URL for the VSIX file
        getDownloadUrl: function () {
            return `https://${this.identifier.split(".")[0]}.gallery.vsassets.io/_apis/public/gallery/publisher/${this.identifier.split(".")[0]}/extension/${this.identifier.split(".")[1]}/${this.version}/assetbyname/Microsoft.VisualStudio.Services.VSIXPackage`;
        },
        // Function to get the filename for the downloaded VSIX file
        getFileName: function () {
            return `${this.identifier}_${this.version}.vsix`;
        },
        // Function to create the download button element
        getDownloadButton: function () {
            const button = document.createElement("a");
            button.innerHTML = "Download VSIX";
            button.style.fontFamily = "wf_segoe-ui,Helvetica Neue,Helvetica,Arial,Verdana";
            button.style.display = "inline-block";
            button.style.padding = "10px 20px"; // Increased padding for a bigger button
            button.style.background = "darkgreen";
            button.style.color = "white";
            button.style.fontWeight = "bold";
            button.style.fontSize = "16px"; // Increased font size
            button.style.margin = "2px 5px";
            button.style.textDecoration = "none"; // Remove default link underline

            // Store the download URL and filename in data attributes
            button.setAttribute("data-download-url", this.getDownloadUrl());
            button.setAttribute("data-download-filename", this.getFileName());

            // Event handler for when the button is clicked
            button.onclick = function (event) {
                const downloadUrl = event.target.getAttribute("data-download-url");
                const downloadFilename = event.target.getAttribute("data-download-filename");

                // Create a temporary link element
                const link = document.createElement("a");
                link.href = downloadUrl;
                link.download = downloadFilename;

                // Trigger the download
                link.click();
            };

            return button;
        }
    };

    // Map to associate metadata table headers with extension data keys
    const metadataMap = {
        "version": "version",
        "unique-identifier": "identifier"
    };

    const getMetadata = function () {
        console.log('Trying to get metadata');
        let cnt = 0;

        // Select all rows in the metadata table
        const metadataRows = document.querySelectorAll(".ux-table-metadata tr");

        // Iterate through each row to extract extension data
        for (let i = 0; i < metadataRows.length; i++) {
            const row = metadataRows[i];
            const cells = row.querySelectorAll("td");
            if (cells.length > 1) {
                const key = cells[0].id;
                const value = cells[1].innerText.trim();
                if (metadataMap.hasOwnProperty(key)) {
                    console.log('Got', key, value);
                    extensionData[metadataMap[key]] = value;
                    ++cnt;
                }
            }
        }
        if (cnt < Object.keys(metadataMap).length) {
            console.log("Couldn't get all metadata, planning retry");
            setTimeout(getMetadata, 1000);
        } else {
            // Find the element with the class "vscode-moreinformation"
            const moreInfoElement = document.querySelector(".vscode-moreinformation");
            if (moreInfoElement) {
                // Append the download button to the parent element
                moreInfoElement.parentElement.appendChild(extensionData.getDownloadButton());
            } else {
                console.error("Element with class 'vscode-moreinformation' not found.");
            }
        }
    };
    getMetadata();
})();
