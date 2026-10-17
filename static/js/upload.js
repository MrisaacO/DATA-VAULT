/*
 * Section 4 of the Development Guide: "Upload one or many files, with
 * progress feedback for large uploads." Progresses via XMLHttpRequest so
 * we get upload.onprogress events; a plain <form> submit gives no such
 * feedback. Falls back to a normal form submission if JS fails for any
 * reason (the <form> still has a valid method/action).
 */
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("upload-form");
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("id_files");
    const progressWrap = document.getElementById("upload-progress-wrap");
    const progressBar = document.getElementById("upload-progress-bar");
    const fileListEl = document.getElementById("selected-file-list");

    if (!form || !fileInput) {
        return;
    }

    function renderSelectedFiles() {
        if (!fileListEl) return;
        fileListEl.innerHTML = "";
        Array.from(fileInput.files || []).forEach(function (file) {
            const li = document.createElement("li");
            li.className = "list-group-item d-flex justify-content-between";
            li.innerHTML = "<span>" + file.name + "</span><span class='text-muted'>" +
                (file.size / (1024 * 1024)).toFixed(2) + " MB</span>";
            fileListEl.appendChild(li);
        });
    }

    fileInput.addEventListener("change", renderSelectedFiles);

    if (dropZone) {
        ["dragenter", "dragover"].forEach(function (evtName) {
            dropZone.addEventListener(evtName, function (e) {
                e.preventDefault();
                dropZone.classList.add("dragover");
            });
        });
        ["dragleave", "drop"].forEach(function (evtName) {
            dropZone.addEventListener(evtName, function (e) {
                e.preventDefault();
                dropZone.classList.remove("dragover");
            });
        });
        dropZone.addEventListener("drop", function (e) {
            if (e.dataTransfer && e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                renderSelectedFiles();
            }
        });
        dropZone.addEventListener("click", function () {
            fileInput.click();
        });
    }

    form.addEventListener("submit", function (e) {
        if (!fileInput.files || fileInput.files.length === 0) {
            return; // let normal validation handle the empty case
        }
        e.preventDefault();

        const formData = new FormData(form);
        const xhr = new XMLHttpRequest();
        xhr.open(form.method, form.action || window.location.href, true);

        if (progressWrap) progressWrap.classList.remove("d-none");

        xhr.upload.addEventListener("progress", function (evt) {
            if (evt.lengthComputable && progressBar) {
                const percent = Math.round((evt.loaded / evt.total) * 100);
                progressBar.style.width = percent + "%";
                progressBar.textContent = percent + "%";
            }
        });

        xhr.onload = function () {
            // Reload to the redirected page (Django redirects after a
            // successful POST); a full navigation also picks up the
            // Django messages framework's success/error banners.
            if (xhr.responseURL) {
                window.location.href = xhr.responseURL;
            } else {
                window.location.reload();
            }
        };

        xhr.onerror = function () {
            if (progressWrap) progressWrap.classList.add("d-none");
            alert("Upload failed. Please check your connection and try again.");
        };

        xhr.send(formData);
    });
});
