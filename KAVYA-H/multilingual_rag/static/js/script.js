document.addEventListener("DOMContentLoaded", () => {
    const maxUploadBytes = 5 * 1024 * 1024;
    const fileInput = document.getElementById("fileInput");
    const uploadArea = document.getElementById("uploadArea");
    const fileList = document.getElementById("fileList");
    const uploadBtn = document.getElementById("uploadBtn");
    const uploadStatus = document.getElementById("uploadStatus");
    const indexSummary = document.getElementById("indexSummary");
    const documentFilter = document.getElementById("documentFilter");
    const questionEl = document.getElementById("question");
    const languageEl = document.getElementById("language");
    const runBtn = document.getElementById("runBtn");
    const queryStatus = document.getElementById("queryStatus");
    const answerBox = document.getElementById("answerBox");
    let selectedFiles = [];
    let indexReady = false;
    let uploadInProgress = false;
    let queryInProgress = false;

    ["dragenter", "dragover"].forEach(eventName => {
        uploadArea.addEventListener(eventName, event => {
            event.preventDefault();
            uploadArea.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach(eventName => {
        uploadArea.addEventListener(eventName, event => {
            event.preventDefault();
            uploadArea.classList.remove("dragover");
        });
    });

    uploadArea.addEventListener("drop", event => {
        addFiles(Array.from(event.dataTransfer.files));
    });

    fileInput.addEventListener("change", () => {
        addFiles(Array.from(fileInput.files));
        fileInput.value = "";
    });

    function setStatus(element, message, kind = "") {
        element.className = `status${kind ? ` ${kind}` : ""}`;
        element.textContent = message;
    }

    function refreshButtons() {
        uploadBtn.disabled = selectedFiles.length === 0 || uploadInProgress;
        runBtn.disabled = !indexReady || queryInProgress || uploadInProgress;
    }

    function addFiles(files) {
        const allowed = [".pdf", ".docx", ".txt"];
        const messages = [];

        for (const file of files) {
            const extension = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
            if (!allowed.includes(extension)) {
                messages.push(`${file.name}: unsupported file type.`);
                continue;
            }
            if (selectedFiles.some(item => item.name === file.name && item.size === file.size)) {
                continue;
            }
            const totalBytes = selectedFiles.reduce((sum, item) => sum + item.size, 0) + file.size;
            if (totalBytes > maxUploadBytes) {
                messages.push(`${file.name}: the total upload limit is 5 MB.`);
                continue;
            }
            selectedFiles.push(file);
        }

        renderFileList();
        refreshButtons();
        setStatus(uploadStatus, messages.join(" "), messages.length ? "error" : "");
    }

    function renderFileList() {
        fileList.replaceChildren();

        selectedFiles.forEach((file, index) => {
            const item = document.createElement("div");
            item.className = "file-item";

            const name = document.createElement("span");
            name.className = "file-name";
            name.textContent = file.name;

            const removeButton = document.createElement("button");
            removeButton.type = "button";
            removeButton.className = "remove-file";
            removeButton.textContent = "Remove";
            removeButton.setAttribute("aria-label", `Remove ${file.name}`);
            removeButton.addEventListener("click", () => {
                selectedFiles.splice(index, 1);
                renderFileList();
                refreshButtons();
            });

            item.append(name, removeButton);
            fileList.append(item);
        });
    }

    async function readResponse(response) {
        let data;
        try {
            data = await response.json();
        } catch {
            throw new Error("The server returned an unreadable response. Please try again.");
        }
        if (!response.ok) {
            throw new Error(data.error || "The request failed. Please try again.");
        }
        return data;
    }

    function renderIndex(data) {
        indexReady = data.ready;
        const documentCount = Array.isArray(data.documents) ? data.documents.length : 0;
        indexSummary.textContent = `${documentCount} document(s) indexed · ${data.num_chunks || 0} chunks`;

        const selectedId = documentFilter.value;
        documentFilter.replaceChildren(new Option("All documents", ""));
        (data.documents || []).forEach(document => {
            documentFilter.add(new Option(document.label || document.name, document.id));
        });
        if (selectedId && Array.from(documentFilter.options).some(option => option.value === selectedId)) {
            documentFilter.value = selectedId;
        }

        refreshButtons();
    }

    uploadBtn.addEventListener("click", async () => {
        if (!selectedFiles.length || uploadInProgress) return;

        const formData = new FormData();
        selectedFiles.forEach(file => formData.append("files", file));
        uploadInProgress = true;
        refreshButtons();
        setStatus(uploadStatus, "Uploading and processing documents…", "loading");

        try {
            const response = await fetch("/upload", { method: "POST", body: formData });
            const data = await readResponse(response);
            selectedFiles = [];
            renderFileList();
            setStatus(uploadStatus, `${data.message} (${data.chunks} chunks created)`, "success");
            renderIndex(await readResponse(await fetch("/status")));
        } catch (error) {
            setStatus(uploadStatus, error.message, "error");
        } finally {
            uploadInProgress = false;
            refreshButtons();
        }
    });

    runBtn.addEventListener("click", async () => {
        const question = questionEl.value.trim();
        if (!question) {
            setStatus(queryStatus, "Please enter a question.", "error");
            questionEl.focus();
            return;
        }

        queryInProgress = true;
        refreshButtons();
        setStatus(queryStatus, "Retrieving and generating answer…", "loading");
        answerBox.textContent = "";

        try {
            const response = await fetch("/query", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question,
                    language: languageEl.value,
                    document_id: documentFilter.value
                })
            });
            const data = await readResponse(response);
            answerBox.textContent = data.answer;
            setStatus(queryStatus, "");
        } catch (error) {
            setStatus(queryStatus, error.message, "error");
        } finally {
            queryInProgress = false;
            refreshButtons();
        }
    });

    fetch("/status")
        .then(readResponse)
        .then(data => {
            renderIndex(data);
            if (data.ready) {
                setStatus(uploadStatus, "Your indexed documents are ready. Uploading new files will replace them.", "success");
            }
        })
        .catch(error => {
            indexSummary.textContent = "Could not load index status.";
            setStatus(uploadStatus, error.message, "error");
        });
});
