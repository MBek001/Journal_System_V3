// Global variables - wait for DOM to be ready
let JOURNAL_ID
let currentPage = 1
let deleteCallback

// Quill editors storage
const quillEditors = {}

// Wait for all scripts to load
document.addEventListener("DOMContentLoaded", () => {
    // Wait for Bootstrap and Quill to be available
    if (typeof bootstrap === "undefined" || typeof Quill === "undefined") {
        console.error("Bootstrap or Quill not loaded yet, retrying...")
        setTimeout(() => {
            if (typeof bootstrap !== "undefined" && typeof Quill !== "undefined") {
                initializeApp()
            } else {
                console.error("Bootstrap or Quill failed to load")
            }
        }, 1000)
        return
    }

    initializeApp()
})

function initializeApp() {
    // Get journal ID from data attribute
    JOURNAL_ID = Number.parseInt(document.body.getAttribute("data-journal-id"))
    if (!JOURNAL_ID) {
        console.error("Journal ID not found!")
        return
    }

    // Initialize Quill editors first
    initializeQuillEditors()

    // Now initialize everything
    loadIssues()
    loadArticles()
    setupForms()
    setupEventListeners()
    setupFileUpload()
    loadEditorTypes()
    loadPolicyTypes()
    loadAuthorsForDropdown();

    // Set current dates
    const currentYear = new Date().getFullYear()
    const currentDate = new Date().toISOString().split("T")[0]
    const issueYear = document.getElementById("issue_year")
    const articleDate = document.getElementById("article_date_published")
    const policyDate = document.getElementById("policy_effective_date")

    if (issueYear) issueYear.value = currentYear
    if (articleDate) articleDate.value = currentDate
    if (policyDate) policyDate.value = currentDate
}

// ===============================
// QUILL EDITOR INITIALIZATION
// ===============================
function initializeQuillEditors() {
    // Journal description editor
    if (document.getElementById("journal-description-editor")) {
        quillEditors.journalDescription = new Quill("#journal-description-editor", {
            theme: "snow",
            modules: {
                toolbar: [
                    [{header: [1, 2, 3, false]}],
                    ["bold", "italic", "underline"],
                    [{list: "ordered"}, {list: "bullet"}],
                    ["link"],
                    ["clean"],
                ],
            },
        })

        // Sync with hidden textarea
        const journalDescTextarea = document.getElementById("journal_description")
        if (journalDescTextarea) {
            // Load existing content
            if (journalDescTextarea.value) {
                quillEditors.journalDescription.root.innerHTML = journalDescTextarea.value
            }

            // Sync on change
            quillEditors.journalDescription.on("text-change", () => {
                journalDescTextarea.value = quillEditors.journalDescription.root.innerHTML
            })
        }
    }

    // Issue description editor (Add)
    if (document.getElementById("issue-description-editor")) {
        quillEditors.issueDescription = new Quill("#issue-description-editor", {
            theme: "snow",
            modules: {
                toolbar: [["bold", "italic", "underline"], [{list: "ordered"}, {list: "bullet"}], ["link"], ["clean"]],
            },
        })

        quillEditors.issueDescription.on("text-change", () => {
            const textarea = document.getElementById("issue_description")
            if (textarea) {
                textarea.value = quillEditors.issueDescription.root.innerHTML
            }
        })
    }

    // Issue description editor (Edit)
    if (document.getElementById("edit-issue-description-editor")) {
        quillEditors.editIssueDescription = new Quill("#edit-issue-description-editor", {
            theme: "snow",
            modules: {
                toolbar: [["bold", "italic", "underline"], [{list: "ordered"}, {list: "bullet"}], ["link"], ["clean"]],
            },
        })

        quillEditors.editIssueDescription.on("text-change", () => {
            const textarea = document.querySelector('#editIssueForm textarea[name="description"]')
            if (textarea) {
                textarea.value = quillEditors.editIssueDescription.root.innerHTML
            }
        })
    }

    // Article abstract editor (Add)
    if (document.getElementById("article-abstract-editor")) {
        quillEditors.articleAbstract = new Quill("#article-abstract-editor", {
            theme: "snow",
            modules: {
                toolbar: [["bold", "italic", "underline"], [{list: "ordered"}, {list: "bullet"}], ["link"], ["clean"]],
            },
        })

        quillEditors.articleAbstract.on("text-change", () => {
            const textarea = document.getElementById("article_abstract")
            if (textarea) {
                textarea.value = quillEditors.articleAbstract.root.innerHTML
            }
        })
    }

    // Article references editor (Add)
    if (document.getElementById("article-references-editor")) {
        quillEditors.articleReferences = new Quill("#article-references-editor", {
            theme: "snow",
            modules: {
                toolbar: [
                    [{header: [1, 2, 3, false]}],
                    ["bold", "italic", "underline"],
                    [{list: "ordered"}, {list: "bullet"}],
                    ["link", "blockquote"],
                    ["clean"]
                ],
            },
        })
        quillEditors.articleReferences.on("text-change", () => {
            const textarea = document.getElementById("article_references")
            if (textarea) {
                textarea.value = quillEditors.articleReferences.root.innerHTML
            }
        })
    }

// Article references editor (Edit)
    if (document.getElementById("edit-article-references-editor")) {
        quillEditors.editArticleReferences = new Quill("#edit-article-references-editor", {
            theme: "snow",
            modules: {
                toolbar: [
                    [{header: [1, 2, 3, false]}],
                    ["bold", "italic", "underline"],
                    [{list: "ordered"}, {list: "bullet"}],
                    ["link", "blockquote"],
                    ["clean"]
                ],
            },
        })
        quillEditors.editArticleReferences.on("text-change", () => {
            const textarea = document.getElementById("edit-references")
            if (textarea) {
                textarea.value = quillEditors.editArticleReferences.root.innerHTML
            }
        })
    }

    // Article abstract editor (Edit)
    if (document.getElementById("edit-article-abstract-editor")) {
        quillEditors.editArticleAbstract = new Quill("#edit-article-abstract-editor", {
            theme: "snow",
            modules: {
                toolbar: [["bold", "italic", "underline"], [{list: "ordered"}, {list: "bullet"}], ["link"], ["clean"]],
            },
        })

        quillEditors.editArticleAbstract.on("text-change", () => {
            const textarea = document.getElementById("edit-abstract")
            if (textarea) {
                textarea.value = quillEditors.editArticleAbstract.root.innerHTML
            }
        })
    }

    // Policy editors (Add)
    initializePolicyEditors("add")
}

function initializePolicyEditors(mode = "add") {
    const prefix = mode === "edit" ? "edit-" : ""

    // Policy short description
    const shortDescId = `${prefix}policy-short-description-editor`
    if (document.getElementById(shortDescId)) {
        quillEditors[`${mode}PolicyShortDescription`] = new Quill(`#${shortDescId}`, {
            theme: "snow",
            modules: {
                toolbar: [["bold", "italic", "underline"], ["clean"]],
            },
        })

        quillEditors[`${mode}PolicyShortDescription`].on("text-change", () => {
            const textarea =
                mode === "edit"
                    ? document.querySelector('#editPolicyForm textarea[name="short_description"]')
                    : document.getElementById("policy_short_description")
            if (textarea) {
                textarea.value = quillEditors[`${mode}PolicyShortDescription`].root.innerHTML
            }
        })
    }

    // Policy content
    const contentId = `${prefix}policy-content-editor`
    if (document.getElementById(contentId)) {
        quillEditors[`${mode}PolicyContent`] = new Quill(`#${contentId}`, {
            theme: "snow",
            modules: {
                toolbar: [
                    [{header: [1, 2, 3, false]}],
                    ["bold", "italic", "underline"],
                    [{list: "ordered"}, {list: "bullet"}],
                    ["link"],
                    ["blockquote"],
                    ["clean"],
                ],
            },
        })

        quillEditors[`${mode}PolicyContent`].on("text-change", () => {
            const textarea =
                mode === "edit"
                    ? document.querySelector('#editPolicyForm textarea[name="content"]')
                    : document.getElementById("policy_content")
            if (textarea) {
                textarea.value = quillEditors[`${mode}PolicyContent`].root.innerHTML
            }
        })
    }

    // Policy requirements
    const reqId = `${prefix}policy-requirements-editor`
    if (document.getElementById(reqId)) {
        quillEditors[`${mode}PolicyRequirements`] = new Quill(`#${reqId}`, {
            theme: "snow",
            modules: {
                toolbar: [["bold", "italic", "underline"], [{list: "ordered"}, {list: "bullet"}], ["link"], ["clean"]],
            },
        })

        quillEditors[`${mode}PolicyRequirements`].on("text-change", () => {
            const textarea =
                mode === "edit"
                    ? document.querySelector('#editPolicyForm textarea[name="requirements"]')
                    : document.getElementById("policy_requirements")
            if (textarea) {
                textarea.value = quillEditors[`${mode}PolicyRequirements`].root.innerHTML
            }
        })
    }

    // Policy examples
    const examplesId = `${prefix}policy-examples-editor`
    if (document.getElementById(examplesId)) {
        quillEditors[`${mode}PolicyExamples`] = new Quill(`#${examplesId}`, {
            theme: "snow",
            modules: {
                toolbar: [["bold", "italic", "underline"], [{list: "ordered"}, {list: "bullet"}], ["link"], ["clean"]],
            },
        })

        quillEditors[`${mode}PolicyExamples`].on("text-change", () => {
            const textarea =
                mode === "edit"
                    ? document.querySelector('#editPolicyForm textarea[name="examples"]')
                    : document.getElementById("policy_examples")
            if (textarea) {
                textarea.value = quillEditors[`${mode}PolicyExamples`].root.innerHTML
            }
        })
    }
}

// Sync all Quill editors with their textareas
// Sync all Quill editors with their textareas
function syncAllQuillEditors() {
    // Journal
    if (quillEditors.journalDescription) {
        const textarea = document.getElementById("journal_description")
        if (textarea) textarea.value = quillEditors.journalDescription.root.innerHTML.trim()
    }

    // Issue
    if (quillEditors.issueDescription) {
        const textarea = document.getElementById("issue_description")
        if (textarea) textarea.value = quillEditors.issueDescription.root.innerHTML.trim()
    }
    if (quillEditors.editIssueDescription) {
        const textarea = document.querySelector('#editIssueForm textarea[name="description"]')
        if (textarea) textarea.value = quillEditors.editIssueDescription.root.innerHTML.trim()
    }

    // Article
    if (quillEditors.articleAbstract) {
        const textarea = document.getElementById("article_abstract")
        if (textarea) textarea.value = quillEditors.articleAbstract.root.innerHTML.trim()
    }
    if (quillEditors.editArticleAbstract) {
        const textarea = document.getElementById("edit-abstract")
        if (textarea) textarea.value = quillEditors.editArticleAbstract.root.innerHTML.trim()
    }
    if (quillEditors.articleReferences) {
        const textarea = document.getElementById("article_references")
        if (textarea) textarea.value = quillEditors.articleReferences.root.innerHTML.trim()
    }
    if (quillEditors.editArticleReferences) {
        const textarea = document.getElementById("edit-references")
        if (textarea) textarea.value = quillEditors.editArticleReferences.root.innerHTML.trim()
    }

    // Policy (add)
    if (quillEditors.addPolicyShortDescription) {
        const textarea = document.getElementById("policy_short_description")
        if (textarea) textarea.value = quillEditors.addPolicyShortDescription.root.innerHTML.trim()
    }
    if (quillEditors.addPolicyContent) {
        const textarea = document.getElementById("policy_content")
        if (textarea) textarea.value = quillEditors.addPolicyContent.root.innerHTML.trim()
    }
    if (quillEditors.addPolicyRequirements) {
        const textarea = document.getElementById("policy_requirements")
        if (textarea) textarea.value = quillEditors.addPolicyRequirements.root.innerHTML.trim()
    }
    if (quillEditors.addPolicyExamples) {
        const textarea = document.getElementById("policy_examples")
        if (textarea) textarea.value = quillEditors.addPolicyExamples.root.innerHTML.trim()
    }

    // Policy (edit)
    if (quillEditors.editPolicyShortDescription) {
        const textarea = document.querySelector('#editPolicyForm textarea[name="short_description"]')
        if (textarea) textarea.value = quillEditors.editPolicyShortDescription.root.innerHTML.trim()
    }
    if (quillEditors.editPolicyContent) {
        const textarea = document.querySelector('#editPolicyForm textarea[name="content"]')
        if (textarea) textarea.value = quillEditors.editPolicyContent.root.innerHTML.trim()
    }
    if (quillEditors.editPolicyRequirements) {
        const textarea = document.querySelector('#editPolicyForm textarea[name="requirements"]')
        if (textarea) textarea.value = quillEditors.editPolicyRequirements.root.innerHTML.trim()
    }
    if (quillEditors.editPolicyExamples) {
        const textarea = document.querySelector('#editPolicyForm textarea[name="examples"]')
        if (textarea) textarea.value = quillEditors.editPolicyExamples.root.innerHTML.trim()
    }
}


// ===============================
// INITIALIZATION FUNCTIONS
// ===============================
function toggleActive(issueId, currentlyActive) {
    fetch(`/admin/ajax/issues/${issueId}/toggle-active/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken(),
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `make_active=${!currentlyActive}`,
    })
        .then((r) => r.json())
        .then((data) => {
            if (data.success) {
                loadIssues(currentPage)
            } else {
                showAlert("Xatolik: " + data.error, "error")
            }
        })
}

// Load editor types for dropdowns
function loadEditorTypes() {
    fetch("/admin/editor-types/")
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                const selects = document.querySelectorAll('select[name="editor_type"]')
                selects.forEach((select) => {
                    select.innerHTML = '<option value="">Tanlang...</option>'
                    data.editor_types.forEach((type) => {
                        const option = document.createElement("option")
                        option.value = type.value
                        option.textContent = type.label
                        select.appendChild(option)
                    })
                })
            }
        })
        .catch((error) => console.error("Error loading editor types:", error))
}

// Load policy types for dropdowns
function loadPolicyTypes() {
    fetch("/admin/policy-types/")
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                const selects = document.querySelectorAll('select[name="policy_type"]')
                selects.forEach((select) => {
                    select.innerHTML = '<option value="">Tanlang...</option>'
                    data.policy_types.forEach((type) => {
                        const option = document.createElement("option")
                        option.value = type.value
                        option.textContent = type.label
                        select.appendChild(option)
                    })
                })
            }
        })
        .catch((error) => console.error("Error loading policy types:", error))
}

// ===============================
// EDITORS MANAGEMENT
// ===============================
// Load editors for this journal
function loadEditors() {
    const loadingDiv = document.getElementById("editors-loading")
    const editorsList = document.getElementById("editors-list")
    const noEditorsMsg = document.getElementById("no-editors-message")

    if (loadingDiv) loadingDiv.style.display = "flex"
    if (editorsList) editorsList.innerHTML = ""
    if (noEditorsMsg) noEditorsMsg.style.display = "none"

    fetch(`/admin/journals/${JOURNAL_ID}/editors/`)
        .then((response) => response.json())
        .then((data) => {
            if (loadingDiv) loadingDiv.style.display = "none"
            if (data.success) {
                updateEditorsList(data.editors)
            } else {
                showAlert("Tahrirchilarni yuklashda xatolik: " + data.error, "error")
            }
        })
        .catch((error) => {
            if (loadingDiv) loadingDiv.style.display = "none"
            showAlert("Xatolik: " + error.message, "error")
        })
}

// Update editors list display
function updateEditorsList(editors) {
    const editorsList = document.getElementById("editors-list")
    const noEditorsMsg = document.getElementById("no-editors-message")

    if (!editors || editors.length === 0) {
        if (noEditorsMsg) noEditorsMsg.style.display = "block"
        return
    }

    if (noEditorsMsg) noEditorsMsg.style.display = "none"

    let html = ""
    editors.forEach((editor) => {
        html += `
            <div class="editor-card">
                <div class="row align-items-center">
                    <div class="col">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h6 class="mb-1">${escapeHtml(editor.full_name)}</h6>
                                <span class="badge badge-editor-type bg-primary me-2">${escapeHtml(editor.editor_type_display)}</span>
                                ${editor.is_active ? '<span class="badge bg-success">Faol</span>' : '<span class="badge bg-secondary">Nofaol</span>'}
                                
                                ${
            editor.title || editor.affiliation || editor.position
                ? `
                                    <div class="mt-2">
                                        ${editor.title ? `<small class="text-muted d-block"><strong>Unvon:</strong> ${escapeHtml(editor.title)}</small>` : ""}
                                        ${editor.affiliation ? `<small class="text-muted d-block"><strong>Tashkilot:</strong> ${escapeHtml(editor.affiliation)}</small>` : ""}
                                        ${editor.position ? `<small class="text-muted d-block"><strong>Lavozim:</strong> ${escapeHtml(editor.position)}</small>` : ""}
                                    </div>
                                `
                : ""
        }
                                
                                <small class="text-muted mt-2 d-block">
                                    <i class="fas fa-calendar me-1"></i>Qo'shilgan: ${editor.created_at}
                                </small>
                            </div>
                            <div class="btn-group" role="group">
                                <button class="btn btn-sm btn-primary edit-editor" data-id="${editor.id}" title="Tahrirlash">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-sm btn-danger delete-editor" data-id="${editor.id}" title="O'chirish">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `
    })

    editorsList.innerHTML = html

    // Add event listeners
    document.querySelectorAll(".edit-editor").forEach((btn) => {
        btn.addEventListener("click", () => editEditor(btn.dataset.id))
    })
    document.querySelectorAll(".delete-editor").forEach((btn) => {
        btn.addEventListener("click", () => deleteEditor(btn.dataset.id))
    })
}

// Edit editor
function editEditor(editorId) {
    fetch(`/admin/journals/${JOURNAL_ID}/editors/${editorId}/update/`)
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                const editor = data.editor
                const form = document.getElementById("editEditorForm")

                // Populate form fields
                form.querySelector('[name="editor_id"]').value = editor.id
                form.querySelector('[name="first_name"]').value = editor.first_name
                form.querySelector('[name="middle_name"]').value = editor.middle_name || ""
                form.querySelector('[name="last_name"]').value = editor.last_name
                form.querySelector('[name="title"]').value = editor.title || ""
                form.querySelector('[name="affiliation"]').value = editor.affiliation || ""
                form.querySelector('[name="position"]').value = editor.position || ""
                form.querySelector('[name="editor_type"]').value = editor.editor_type
                form.querySelector('[name="order"]').value = editor.order
                form.querySelector('[name="is_active"]').checked = editor.is_active

                // Check if bootstrap is available before using it
                if (typeof bootstrap !== "undefined") {
                    new bootstrap.Modal(document.getElementById("editEditorModal")).show()
                } else {
                    console.error("Bootstrap not available")
                    showAlert("Xatolik: Bootstrap yuklanmagan", "error")
                }
            } else {
                showAlert("Muharrir ma'lumotlarini olishda xatolik: " + data.error, "error")
            }
        })
        .catch((error) => showAlert("Xatolik: " + error.message, "error"))
}

// Delete editor
function deleteEditor(editorId) {
    showDeleteConfirmation("Muharrir", () => {
        fetch(`/admin/journals/${JOURNAL_ID}/editors/${editorId}/delete/`, {
            method: "POST",
            headers: {"X-CSRFToken": getCSRFToken()},
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    showAlert("Muharrir o'chirildi!", "success")
                    loadEditors()
                } else {
                    showAlert("Xatolik: " + data.error, "error")
                }
            })
            .catch((error) => showAlert("Xatolik: " + error.message, "error"))
    })
}

// ===============================
// POLICIES MANAGEMENT
// ===============================
// Load policies for this journal
function loadPolicies() {
    const loadingDiv = document.getElementById("policies-loading")
    const policiesList = document.getElementById("policies-list")
    const noPoliciesMsg = document.getElementById("no-policies-message")

    if (loadingDiv) loadingDiv.style.display = "flex"
    if (policiesList) policiesList.innerHTML = ""
    if (noPoliciesMsg) noPoliciesMsg.style.display = "none"

    fetch(`/admin/journals/${JOURNAL_ID}/policies/`)
        .then((response) => response.json())
        .then((data) => {
            if (loadingDiv) loadingDiv.style.display = "none"
            if (data.success) {
                updatePoliciesList(data.policies)
            } else {
                showAlert("Siyosatlarni yuklashda xatolik: " + data.error, "error")
            }
        })
        .catch((error) => {
            if (loadingDiv) loadingDiv.style.display = "none"
            showAlert("Xatolik: " + error.message, "error")
        })
}

// Update policies list display
function updatePoliciesList(policies) {
    const policiesList = document.getElementById("policies-list")
    const noPoliciesMsg = document.getElementById("no-policies-message")

    if (!policies || policies.length === 0) {
        if (noPoliciesMsg) noPoliciesMsg.style.display = "block"
        return
    }

    if (noPoliciesMsg) noPoliciesMsg.style.display = "none"

    let html = ""
    policies.forEach((policy) => {
        html += `
            <div class="policy-card">
                <div class="d-flex justify-content-between align-items-start mb-3">
                    <div>
                        <h6 class="mb-2">${escapeHtml(policy.title)}</h6>
                        <span class="badge bg-info me-2">${escapeHtml(policy.policy_type_display)}</span>
                        ${policy.is_active ? '<span class="badge bg-success">Faol</span>' : '<span class="badge bg-secondary">Nofaol</span>'}
                        ${policy.is_public ? '<span class="badge bg-primary ms-1">Ommaviy</span>' : '<span class="badge bg-warning ms-1">Maxfiy</span>'}
                    </div>
                    <div class="btn-group" role="group">
                        <button class="btn btn-sm btn-success view-policy" data-id="${policy.id}" title="Ko'rish">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-primary edit-policy" data-id="${policy.id}" title="Tahrirlash">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-danger delete-policy" data-id="${policy.id}" title="O'chirish">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                
                ${policy.short_description ? `<p class="text-muted mb-2">${escapeHtml(policy.short_description)}</p>` : ""}
                
                <div class="content-preview">
                    <small class="text-muted">Mazmun:</small>
                    <p class="mb-0">${escapeHtml(policy.content_preview)}</p>
                </div>
                
                <div class="policy-meta mt-3">
                    <small class="text-muted">
                        <i class="fas fa-language me-1"></i>${policy.language.toUpperCase()}
                        <i class="fas fa-tag ms-3 me-1"></i>v${policy.version}
                        <i class="fas fa-calendar ms-3 me-1"></i>${policy.effective_date}
                        <i class="fas fa-word ms-3 me-1"></i>${policy.word_count} so'z
                        ${policy.last_updated ? `<i class="fas fa-clock ms-3 me-1"></i>${policy.last_updated}` : ""}
                    </small>
                </div>
            </div>
        `
    })

    policiesList.innerHTML = html

    // Add event listeners
    document.querySelectorAll(".view-policy").forEach((btn) => {
        btn.addEventListener("click", () => viewPolicy(btn.dataset.id))
    })
    document.querySelectorAll(".edit-policy").forEach((btn) => {
        btn.addEventListener("click", () => editPolicy(btn.dataset.id))
    })
    document.querySelectorAll(".delete-policy").forEach((btn) => {
        btn.addEventListener("click", () => deletePolicy(btn.dataset.id))
    })
}

// View policy details
function viewPolicy(policyId) {
    fetch(`/admin/journals/${JOURNAL_ID}/policies/${policyId}/update/`)
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                const policy = data.policy
                const html = `
                    <div class="modal fade" id="viewPolicyModal" tabindex="-1">
                        <div class="modal-dialog modal-xl">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">
                                        <i class="fas fa-gavel me-2"></i>${escapeHtml(policy.title)}
                                    </h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <div class="row">
                                        <div class="col-md-8">
                                            ${
                    policy.short_description
                        ? `
                                                <div class="alert alert-info">
                                                    <strong>Qisqacha:</strong> ${escapeHtml(policy.short_description)}
                                                </div>
                                            `
                        : ""
                }
                                            
                                            <h6 class="text-primary">Asosiy Mazmun</h6>
                                            <div class="content-preview">
                                                ${escapeHtml(policy.content).replace(/\n/g, "<br>")}
                                            </div>
                                            
                                            ${
                    policy.requirements
                        ? `
                                                <h6 class="text-primary mt-4">Talablar</h6>
                                                <div class="content-preview">
                                                    ${escapeHtml(policy.requirements).replace(/\n/g, "<br>")}
                                                </div>
                                            `
                        : ""
                }
                                            
                                            ${
                    policy.examples
                        ? `
                                                <h6 class="text-primary mt-4">Misollar</h6>
                                                <div class="content-preview">
                                                    ${escapeHtml(policy.examples).replace(/\n/g, "<br>")}
                                                </div>
                                            `
                        : ""
                }
                                        </div>
                                        <div class="col-md-4">
                                            <h6 class="text-primary">Ma'lumotlar</h6>
                                            <p><strong>Turi:</strong> <span class="badge bg-primary">${escapeHtml(policy.policy_type_display || policy.policy_type)}</span></p>
                                            <p><strong>Til:</strong> ${policy.language.toUpperCase()}</p>
                                            <p><strong>Versiya:</strong> ${policy.version}</p>
                                            <p><strong>Holat:</strong> ${policy.is_active ? '<span class="badge bg-success">Faol</span>' : '<span class="badge bg-secondary">Nofaol</span>'}</p>
                                            <p><strong>Ko'rinish:</strong> ${policy.is_public ? '<span class="badge bg-primary">Ommaviy</span>' : '<span class="badge bg-warning">Maxfiy</span>'}</p>
                                            <p><strong>Kuchga kirgan:</strong> ${policy.effective_date}</p>
                                            <p><strong>So'zlar soni:</strong> ${policy.word_count}</p>
                                            ${policy.created_by ? `<p><strong>Yaratuvchi:</strong> ${escapeHtml(policy.created_by)}</p>` : ""}
                                            ${policy.updated_by ? `<p><strong>Yangilovchi:</strong> ${escapeHtml(policy.updated_by)}</p>` : ""}
                                            
                                            ${
                    policy.keywords
                        ? `
                                                <h6 class="text-primary mt-3">Kalit so'zlar</h6>
                                                <p><small>${escapeHtml(policy.keywords)}</small></p>
                                            `
                        : ""
                }
                                            
                                            ${
                    policy.meta_description
                        ? `
                                                <h6 class="text-primary mt-3">Meta tavsif</h6>
                                                <p><small>${escapeHtml(policy.meta_description)}</small></p>
                                            `
                        : ""
                }
                                        </div>
                                    </div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-primary" onclick="editPolicy(${policyId}); if(typeof bootstrap !== 'undefined') { bootstrap.Modal.getInstance(document.getElementById('viewPolicyModal')).hide(); }">
                                        <i class="fas fa-edit me-2"></i>Tahrirlash
                                    </button>
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Yopish</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `

                // Remove existing modal if any
                const existingModal = document.getElementById("viewPolicyModal")
                if (existingModal) existingModal.remove()

                // Add new modal to body
                document.body.insertAdjacentHTML("beforeend", html)

                // Show modal
                if (typeof bootstrap !== "undefined") {
                    new bootstrap.Modal(document.getElementById("viewPolicyModal")).show()
                } else {
                    console.error("Bootstrap not available")
                    showAlert("Xatolik: Bootstrap yuklanmagan", "error")
                }
            } else {
                showAlert("Siyosat ma'lumotlarini olishda xatolik: " + data.error, "error")
            }
        })
        .catch((error) => showAlert("Xatolik: " + error.message, "error"))
}

// Edit policy
function editPolicy(policyId) {
    fetch(`/admin/journals/${JOURNAL_ID}/policies/${policyId}/update/`)
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                const policy = data.policy
                const form = document.getElementById("editPolicyForm")

                // Initialize edit policy editors if not already done
                if (!quillEditors.editPolicyContent) {
                    initializePolicyEditors("edit")
                }

                // Populate form fields
                form.querySelector('[name="policy_id"]').value = policy.id
                form.querySelector('[name="policy_type"]').value = policy.policy_type
                form.querySelector('[name="title"]').value = policy.title
                form.querySelector('[name="language"]').value = policy.language
                form.querySelector('[name="meta_description"]').value = policy.meta_description || ""
                form.querySelector('[name="keywords"]').value = policy.keywords || ""
                form.querySelector('[name="version"]').value = policy.version
                form.querySelector('[name="order"]').value = policy.order
                form.querySelector('[name="effective_date"]').value = policy.effective_date
                form.querySelector('[name="is_active"]').checked = policy.is_active
                form.querySelector('[name="is_public"]').checked = policy.is_public

                // Set Quill editor content and sync with textareas
                if (quillEditors.editPolicyShortDescription) {
                    quillEditors.editPolicyShortDescription.root.innerHTML = policy.short_description || ""
                    form.querySelector('[name="short_description"]').value = policy.short_description || ""
                }
                if (quillEditors.editPolicyContent) {
                    quillEditors.editPolicyContent.root.innerHTML = policy.content || ""
                    form.querySelector('[name="content"]').value = policy.content || ""
                }
                if (quillEditors.editPolicyRequirements) {
                    quillEditors.editPolicyRequirements.root.innerHTML = policy.requirements || ""
                    form.querySelector('[name="requirements"]').value = policy.requirements || ""
                }
                if (quillEditors.editPolicyExamples) {
                    quillEditors.editPolicyExamples.root.innerHTML = policy.examples || ""
                    form.querySelector('[name="examples"]').value = policy.examples || ""
                }

                if (typeof bootstrap !== "undefined") {
                    new bootstrap.Modal(document.getElementById("editPolicyModal")).show()
                } else {
                    console.error("Bootstrap not available")
                    showAlert("Xatolik: Bootstrap yuklanmagan", "error")
                }
            } else {
                showAlert("Siyosat ma'lumotlarini olishda xatolik: " + data.error, "error")
            }
        })
        .catch((error) => showAlert("Xatolik: " + error.message, "error"))
}

// Delete policy
function deletePolicy(policyId) {
    showDeleteConfirmation("Siyosat", () => {
        fetch(`/admin/journals/${JOURNAL_ID}/policies/${policyId}/delete/`, {
            method: "POST",
            headers: {"X-CSRFToken": getCSRFToken()},
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    showAlert("Siyosat o'chirildi!", "success")
                    loadPolicies()
                } else {
                    showAlert("Xatolik: " + data.error, "error")
                }
            })
            .catch((error) => showAlert("Xatolik: " + error.message, "error"))
    })
}

// ===============================
// EXISTING FUNCTIONS (ISSUES & ARTICLES)
// ===============================
// Setup file upload functionality
function setupFileUpload() {
    const fileUploadArea = document.getElementById("file-upload-area")
    const fileInput = document.getElementById("article_pdf_file")
    const fileInfo = document.getElementById("file-info")
    const fileName = document.getElementById("file-name")

    if (!fileUploadArea || !fileInput) return

    fileUploadArea.addEventListener("click", () => fileInput.click())

    fileUploadArea.addEventListener("dragover", function (e) {
        e.preventDefault()
        this.classList.add("dragover")
        this.style.borderColor = "#667eea"
        this.style.background = "#f8f9ff"
    })

    fileUploadArea.addEventListener("dragleave", function (e) {
        e.preventDefault()
        this.classList.remove("dragover")
        this.style.borderColor = "#ddd"
        this.style.background = ""
    })

    fileUploadArea.addEventListener("drop", function (e) {
        e.preventDefault()
        this.classList.remove("dragover")
        this.style.borderColor = "#ddd"
        this.style.background = ""

        const files = e.dataTransfer.files
        if (files.length > 0) {
            validateAndShowFile(files[0])
        }
    })

    fileInput.addEventListener("change", function () {
        if (this.files.length > 0) {
            validateAndShowFile(this.files[0])
        }
    })

    function validateAndShowFile(file) {
        const maxSize = 10 * 1024 * 1024 // 10MB

        if (file.type !== "application/pdf") {
            showAlert("Faqat PDF fayllar qabul qilinadi!", "warning")
            fileInput.value = ""
            return
        }

        if (file.size > maxSize) {
            showAlert("Fayl hajmi 10MB dan oshmasligi kerak!", "warning")
            fileInput.value = ""
            return
        }

        if (fileName && fileInfo) {
            fileName.textContent = file.name
            fileInfo.style.display = "block"
            fileUploadArea.querySelector("i").style.display = "none"
            fileUploadArea.querySelector("p").style.display = "none"
        }
    }
}

function hideFileInfo() {
    const fileInfo = document.getElementById("file-info")
    const fileInput = document.getElementById("article_pdf_file")
    const fileUploadArea = document.getElementById("file-upload-area")

    if (fileInfo) fileInfo.style.display = "none"
    if (fileInput) fileInput.value = ""
    if (fileUploadArea) {
        fileUploadArea.querySelector("i").style.display = "block"
        fileUploadArea.querySelector("p").style.display = "block"
    }
}

// Load issues for this journal
function loadIssues(page = 1) {
    currentPage = page
    const loadingDiv = document.getElementById("issues-loading")
    if (loadingDiv) loadingDiv.style.display = "flex"

    fetch(`/admin/journals/${JOURNAL_ID}/issues/?page=${page}`)
        .then((response) => response.json())
        .then((data) => {
            if (loadingDiv) loadingDiv.style.display = "none"
            if (data.success) {
                updateIssuesTable(data.issues)
                updatePagination("issues", data.pagination)
                populateIssueSelects(data.issues)
            } else {
                showAlert("Sonlarni yuklashda xatolik: " + data.error, "error")
            }
        })
        .catch((error) => {
            if (loadingDiv) loadingDiv.style.display = "none"
            showAlert("Xatolik: " + error.message, "error")
        })
}

// Load articles for this journal
function loadArticles(page = 1) {
    const search = document.getElementById("article-search")?.value || ""
    const issueFilter = document.getElementById("article-issue-filter")?.value || ""
    const statusFilter = document.getElementById("article-status-filter")?.value || ""

    const loadingDiv = document.getElementById("articles-loading")
    if (loadingDiv) loadingDiv.style.display = "flex"

    let url = `/admin/journals/${JOURNAL_ID}/articles/?page=${page}`
    if (search) url += `&search=${encodeURIComponent(search)}`
    if (issueFilter) url += `&issue=${issueFilter}`
    if (statusFilter) url += `&status=${statusFilter}`

    fetch(url)
        .then((response) => response.json())
        .then((data) => {
            if (loadingDiv) loadingDiv.style.display = "none"
            if (data.success) {
                updateArticlesTable(data.articles)
                updatePagination("articles", data.pagination)
            } else {
                showAlert("Maqolalarni yuklashda xatolik: " + data.error, "error")
            }
        })
        .catch((error) => {
            if (loadingDiv) loadingDiv.style.display = "none"
            showAlert("Xatolik: " + error.message, "error")
        })
}

function setActiveIssueInfo() {
    const activeIssueInfo = document.getElementById("active-issue-info")
    if (!activeIssueInfo) return

    fetch(`/admin/journals/${JOURNAL_ID}/active-issue/`)
        .then((response) => response.json())
        .then((data) => {
            if (data.success && data.issue) {
                activeIssueInfo.value = `Jild ${data.issue.volume}, Son ${data.issue.number} (${data.issue.year})`
            } else {
                activeIssueInfo.value = "Faol son topilmadi! Avval yangi son yarating."
            }
        })
        .catch((error) => {
            console.error("Error loading active issue:", error)
        })
}

// Update issues table display
function updateIssuesTable(issues) {
    const tbody = document.getElementById("issues-table-body")
    tbody.innerHTML = ""

    if (!issues || !issues.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">Sonlar mavjud emas</td></tr>'
        return
    }

    issues.forEach((issue) => {
        const row = document.createElement("tr")
        row.innerHTML = `
      <td><strong>Jild ${issue.volume}</strong></td>
      <td><strong>Son ${issue.number}</strong></td>
      <td>${issue.year}</td>
      <td>${issue.date_published || '<span class="text-muted">Belgilanmagan</span>'}</td>
      <td><span class="badge bg-info">${issue.article_count || 0}</span></td>
      <td>
        ${
            issue.is_published
                ? '<span class="badge bg-success me-1">Nashr etilgan</span>'
                : '<span class="badge bg-warning me-1">Kutilmoqda</span>'
        }
        ${
            issue.is_active
                ? '<span class="badge bg-primary">Faol</span>'
                : '<span class="badge bg-danger text-light ">Arxivlangan</span>'
        }
      </td>
      <td>
        <div class="btn-group" role="group">
          <button class="btn btn-sm btn-success view-issue" data-id="${issue.id}" title="Ko\'rish">
            <i class="fas fa-eye"></i>
          </button>
          <button class="btn btn-sm btn-primary edit-issue" data-id="${issue.id}" title="Tahrirlash">
            <i class="fas fa-edit"></i>
          </button>
          <button class="btn btn-sm btn-danger delete-issue" data-id="${issue.id}" title="O\'chirish">
            <i class="fas fa-trash"></i>
          </button>
        </div>
      </td>
    `
        tbody.appendChild(row)
    })

    // Re-attach listeners
    document
        .querySelectorAll(".view-issue")
        .forEach((btn) => btn.addEventListener("click", () => viewIssue(btn.dataset.id)))
    document
        .querySelectorAll(".edit-issue")
        .forEach((btn) => btn.addEventListener("click", () => editIssue(btn.dataset.id)))
    document
        .querySelectorAll(".delete-issue")
        .forEach((btn) => btn.addEventListener("click", () => deleteIssue(btn.dataset.id)))
}

// Update articles table
function updateArticlesTable(articles) {
    const tbody = document.getElementById("articles-table-body")
    tbody.innerHTML = ""

    if (!articles || articles.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-4">Maqolalar mavjud emas</td></tr>'
        return
    }

    articles.forEach((article) => {
        const row = document.createElement("tr")
        row.innerHTML = `
            <td>
                <strong>${escapeHtml(article.title)}</strong>
                ${article.subtitle ? `<br><small class="text-muted">${escapeHtml(article.subtitle)}</small>` : ""}
            </td>
            <td>${escapeHtml(article.authors?.join(", ") || "N/A")}</td>
            <td>${escapeHtml(article.issue_info || "N/A")}</td>
            <td>${article.date_published}</td>
            <td><span class="badge bg-info">${article.views || 0}</span></td>
            <td>
                ${article.is_published ? '<span class="badge bg-success">Nashr etilgan</span>' : '<span class="badge bg-warning">Kutilmoqda</span>'}
                ${article.featured ? '<span class="badge bg-warning ms-1">Tanlangan</span>' : ""}
            </td>
            <td>
                <div class="btn-group" role="group">
                    <button class="btn btn-sm btn-success view-article" data-id="${article.id}" title="Ko'rish">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-primary edit-article" data-id="${article.id}" title="Tahrirlash">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger delete-article" data-id="${article.id}" title="O'chirish">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `
        tbody.appendChild(row)
    })

    // Add event listeners for articles
    document.querySelectorAll(".view-article").forEach((btn) => {
        btn.addEventListener("click", () => viewArticle(btn.dataset.id))
    })
    document.querySelectorAll(".edit-article").forEach((btn) => {
        btn.addEventListener("click", () => editArticle(btn.dataset.id))
    })
    document.querySelectorAll(".delete-article").forEach((btn) => {
        btn.addEventListener("click", () => deleteArticle(btn.dataset.id))
    })
}

// Populate issue selects
function populateIssueSelects(issues) {
    const selects = document.querySelectorAll('#article-issue-filter, #article_issue, select[name="issue_id"]')
    selects.forEach((select) => {
        if (select.id === "article-issue-filter") {
            select.innerHTML = '<option value="">Barcha sonlar</option>'
        } else {
            select.innerHTML = '<option value="">Sonni tanlang (yoki yangi son yaratiladi)</option>'
        }

        issues.forEach((issue) => {
            const option = document.createElement("option")
            option.value = issue.id
            option.textContent = `Jild ${issue.volume}, Son ${issue.number} (${issue.year})`
            select.appendChild(option)
        })
    })
}

function setupEditForms() {
    // Edit Issue Form
    const editIssueForm = document.getElementById("editIssueForm")
    if (editIssueForm) {
        editIssueForm.addEventListener("submit", function (e) {
            e.preventDefault()

            // Sync Quill content first
            syncAllQuillEditors()

            const formData = new FormData(this)
            const issueId = formData.get("issue_id")

            const submitBtn =
                this.querySelector('button[type="submit"]') || document.querySelector("#editIssueModal .btn-primary:last-child")

            if (!submitBtn) {
                console.error("Submit button not found for edit issue form")
                return
            }

            const originalText = submitBtn.innerHTML
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...'
            submitBtn.disabled = true

            fetch(`/admin/issues/update/${issueId}/`, {
                method: "POST",
                body: formData,
                headers: {"X-CSRFToken": getCSRFToken()},
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        showAlert("Son muvaffaqiyatli yangilandi!", "success")
                        if (typeof bootstrap !== "undefined") {
                            bootstrap.Modal.getInstance(document.getElementById("editIssueModal")).hide()
                        }
                        loadIssues()
                    } else {
                        showAlert("Xatolik: " + data.error, "error")
                    }
                })
                .catch((error) => showAlert("Xatolik: " + error.message, "error"))
                .finally(() => {
                    submitBtn.innerHTML = originalText
                    submitBtn.disabled = false
                })
        })
    }

    // Edit Article Form
    const editArticleForm = document.getElementById("editArticleForm")
    if (editArticleForm) {
        editArticleForm.addEventListener("submit", function (e) {
            e.preventDefault()

            // Sync Quill content first
            syncAllQuillEditors()

            const formData = new FormData(this)
            const articleId = formData.get("article_id")

            const submitBtn =
                this.querySelector('button[type="submit"]') ||
                document.querySelector("#editArticleModal .btn-primary:last-child")

            if (!submitBtn) {
                console.error("Submit button not found for edit article form")
                return
            }

            const originalText = submitBtn.innerHTML
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...'
            submitBtn.disabled = true

            fetch(`/admin/articles/update/${articleId}/`, {
                method: "POST",
                body: formData,
                headers: {"X-CSRFToken": getCSRFToken()},
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        showAlert("Maqola muvaffaqiyatli yangilandi!", "success")
                        if (typeof bootstrap !== "undefined") {
                            bootstrap.Modal.getInstance(document.getElementById("editArticleModal")).hide()
                        }
                        loadArticles()
                    } else {
                        showAlert("Xatolik: " + data.error, "error")
                    }
                })
                .catch((error) => showAlert("Xatolik: " + error.message, "error"))
                .finally(() => {
                    submitBtn.innerHTML = originalText
                    submitBtn.disabled = false
                })
        })
    }
}

// Setup all forms
function setupForms() {
    // Add Issue Form
    const addIssueForm = document.getElementById("addIssueForm")
    if (addIssueForm) {
        addIssueForm.addEventListener("submit", function (e) {
            e.preventDefault()

            // Sync Quill content first
            syncAllQuillEditors()

            const formData = new FormData(this)

            const submitBtn =
                document.querySelector('#addIssueModal button[type="submit"]') ||
                document.querySelector("#addIssueModal .btn-primary:last-child")

            if (!submitBtn) {
                console.error("Submit button not found for add issue form")
                return
            }

            const originalText = submitBtn.innerHTML
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...'
            submitBtn.disabled = true

            fetch(`/admin/journals/${JOURNAL_ID}/issues/add/`, {
                method: "POST",
                body: formData,
                headers: {"X-CSRFToken": getCSRFToken()},
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        showAlert("Son muvaffaqiyatli qo'shildi!", "success")
                        this.reset()
                        // Clear Quill editor
                        if (quillEditors.issueDescription) {
                            quillEditors.issueDescription.setContents([])
                        }
                        if (typeof bootstrap !== "undefined") {
                            bootstrap.Modal.getInstance(document.getElementById("addIssueModal")).hide()
                        }
                        loadIssues()
                    } else {
                        showAlert("Xatolik: " + data.error, "error")
                    }
                })
                .catch((error) => showAlert("Xatolik: " + error.message, "error"))
                .finally(() => {
                    submitBtn.innerHTML = originalText
                    submitBtn.disabled = false
                })
        })
    }

    // Add Article Form
    const addArticleForm = document.getElementById("addArticleForm")
    if (addArticleForm) {
        addArticleForm.addEventListener("submit", function (e) {
            e.preventDefault()
            // Use setTimeout to ensure DOM is fully updated
            setTimeout(() => { // <-- START of setTimeout
                let isValid = true;
                let firstInvalidField = null;
                // Validate Title
                const titleField = document.getElementById("article_title");
                if (!titleField.value.trim()) {
                    isValid = false;
                    titleField.classList.add("is-invalid");
                    if (!firstInvalidField) firstInvalidField = titleField;
                } else {
                    titleField.classList.remove("is-invalid");
                }
                // Validate Abstract
                const abstractField = document.getElementById("article_abstract");
                if (!abstractField.value.trim()) {
                    isValid = false;
                    abstractField.classList.add("is-invalid");
                    if (!firstInvalidField) firstInvalidField = abstractField;
                } else {
                    abstractField.classList.remove("is-invalid");
                }
                if (quillEditors.articleReferences) {
                    const textarea = document.getElementById("article_references")
                    if (textarea) textarea.value = quillEditors.articleReferences.root.innerHTML
                }

                // Validate PDF
                const pdfFile = document.getElementById("article_pdf_file");
                if (!pdfFile.files.length) {
                    isValid = false;
                    pdfFile.classList.add("is-invalid");
                    if (!firstInvalidField) firstInvalidField = pdfFile;
                } else {
                    pdfFile.classList.remove("is-invalid");
                }
                // Validate at least one author exists with first_name and last_name
                const authorFirstNameFields = document.querySelectorAll('input[name="author_first_name[]"]');
                const authorLastNameFields = document.querySelectorAll('input[name="author_last_name[]"]');
                let hasAtLeastOneValidAuthor = false;
                for (let i = 0; i < authorFirstNameFields.length; i++) {
                    const firstName = authorFirstNameFields[i].value.trim();
                    const lastName = authorLastNameFields[i].value.trim();
                    if (firstName && lastName) {
                        hasAtLeastOneValidAuthor = true;
                        // Clear error state for this row
                        authorFirstNameFields[i].classList.remove("is-invalid");
                        authorLastNameFields[i].classList.remove("is-invalid");
                    } else {
                        // Mark as invalid if empty
                        if (!firstName) authorFirstNameFields[i].classList.add("is-invalid");
                        if (!lastName) authorLastNameFields[i].classList.add("is-invalid");
                        if (!firstInvalidField && (!firstName || !lastName)) {
                            firstInvalidField = firstName ? authorLastNameFields[i] : authorFirstNameFields[i];
                        }
                    }
                }
                if (!hasAtLeastOneValidAuthor) {
                    isValid = false;
                    showAlert("Iltimos, kamida bitta muallifni to'liq ism va familiyasi bilan kiriting.", "error");
                }
                // If not valid, focus the first invalid field and stop submission
                if (!isValid) {
                    if (firstInvalidField) {
                        firstInvalidField.focus();
                    }
                    return; // Stop here, do not submit
                }
                // Remove empty author rows before creating FormData
                document.querySelectorAll('.author-row').forEach(row => {
                    const firstName = row.querySelector('input[name="author_first_name[]"]').value.trim();
                    const lastName = row.querySelector('input[name="author_last_name[]"]').value.trim();
                    if (!firstName && !lastName) {
                        row.remove();
                    }
                });
                // If valid, proceed with form submission
                // Sync Quill content first
                syncAllQuillEditors()
                const formData = new FormData(this)
                const submitBtn =
                    document.querySelector('#addArticleModal button[type="submit"]') ||
                    document.querySelector("#addArticleModal .btn-primary:last-child")
                if (!submitBtn) {
                    console.error("Submit button not found for add article form")
                    return
                }
                const originalText = submitBtn.innerHTML
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...'
                submitBtn.disabled = true
                fetch(`/admin/journals/${JOURNAL_ID}/articles/add/`, {
                    method: "POST",
                    body: formData,
                    headers: {"X-CSRFToken": getCSRFToken()},
                })
                    .then((response) => response.json())
                    .then((data) => {
                        if (data.success) {
                            showAlert("Maqola muvaffaqiyatli qo'shildi!", "success")
                            this.reset()
                            // Clear Quill editor
                            if (quillEditors.articleAbstract) {
                                quillEditors.articleAbstract.setContents([])
                            }
                            hideFileInfo()
                            if (typeof bootstrap !== "undefined") {
                                bootstrap.Modal.getInstance(document.getElementById("addArticleModal")).hide()
                            }
                            loadArticles()
                            loadIssues() // Reload issues to update counts
                        } else {
                            showAlert("Xatolik: " + data.error, "error")
                        }
                    })
                    .catch((error) => showAlert("Xatolik: " + error.message, "error"))
                    .finally(() => {
                        submitBtn.innerHTML = originalText
                        submitBtn.disabled = false
                    })
            }, 0); // <-- END of setTimeout. The '0' is crucial.
        })
    }

    // Add Editor Form
    const addEditorForm = document.getElementById("addEditorForm")
    if (addEditorForm) {
        addEditorForm.addEventListener("submit", function (e) {
            e.preventDefault()
            const formData = new FormData(this)

            const submitBtn =
                document.querySelector('#addEditorModal button[type="submit"]') ||
                document.querySelector("#addEditorModal .btn-primary:last-child")

            if (!submitBtn) {
                console.error("Submit button not found for add editor form")
                return
            }

            const originalText = submitBtn.innerHTML
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...'
            submitBtn.disabled = true

            fetch(`/admin/journals/${JOURNAL_ID}/editors/add/`, {
                method: "POST",
                body: formData,
                headers: {"X-CSRFToken": getCSRFToken()},
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        showAlert("Muharrir muvaffaqiyatli qo'shildi!", "success")
                        this.reset()
                        if (typeof bootstrap !== "undefined") {
                            bootstrap.Modal.getInstance(document.getElementById("addEditorModal")).hide()
                        }
                        loadEditors()
                    } else {
                        showAlert("Xatolik: " + data.error, "error")
                    }
                })
                .catch((error) => showAlert("Xatolik: " + error.message, "error"))
                .finally(() => {
                    submitBtn.innerHTML = originalText
                    submitBtn.disabled = false
                })
        })
    }

    // Edit Editor Form
    const editEditorForm = document.getElementById("editEditorForm")
    if (editEditorForm) {
        editEditorForm.addEventListener("submit", function (e) {
            e.preventDefault()
            const formData = new FormData(this)
            const editorId = formData.get("editor_id")

            const submitBtn =
                document.querySelector('#editEditorModal button[type="submit"]') ||
                document.querySelector("#editEditorModal .btn-primary:last-child")

            if (!submitBtn) {
                console.error("Submit button not found for edit editor form")
                return
            }

            const originalText = submitBtn.innerHTML
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...'
            submitBtn.disabled = true

            fetch(`/admin/journals/${JOURNAL_ID}/editors/${editorId}/update/`, {
                method: "POST",
                body: formData,
                headers: {"X-CSRFToken": getCSRFToken()},
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        showAlert("Muharrir muvaffaqiyatli yangilandi!", "success")
                        if (typeof bootstrap !== "undefined") {
                            bootstrap.Modal.getInstance(document.getElementById("editEditorModal")).hide()
                        }
                        loadEditors()
                    } else {
                        showAlert("Xatolik: " + data.error, "error")
                    }
                })
                .catch((error) => showAlert("Xatolik: " + error.message, "error"))
                .finally(() => {
                    submitBtn.innerHTML = originalText
                    submitBtn.disabled = false
                })
        })
    }

    // Add Policy Form
    const addPolicyForm = document.getElementById("addPolicyForm")
    if (addPolicyForm) {
        addPolicyForm.addEventListener("submit", function (e) {
            e.preventDefault()

            // Sync Quill content first
            syncAllQuillEditors()

            const formData = new FormData(this)

            const submitBtn =
                document.querySelector('#addPolicyModal button[type="submit"]') ||
                document.querySelector("#addPolicyModal .btn-primary:last-child")

            if (!submitBtn) {
                console.error("Submit button not found for add policy form")
                return
            }

            const originalText = submitBtn.innerHTML
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...'
            submitBtn.disabled = true

            fetch(`/admin/journals/${JOURNAL_ID}/policies/add/`, {
                method: "POST",
                body: formData,
                headers: {"X-CSRFToken": getCSRFToken()},
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        showAlert("Siyosat muvaffaqiyatli qo'shildi!", "success")
                        this.reset()
                        // Clear Quill editors
                        if (quillEditors.addPolicyShortDescription) quillEditors.addPolicyShortDescription.setContents([])
                        if (quillEditors.addPolicyContent) quillEditors.addPolicyContent.setContents([])
                        if (quillEditors.addPolicyRequirements) quillEditors.addPolicyRequirements.setContents([])
                        if (quillEditors.addPolicyExamples) quillEditors.addPolicyExamples.setContents([])
                        if (typeof bootstrap !== "undefined") {
                            bootstrap.Modal.getInstance(document.getElementById("addPolicyModal")).hide()
                        }
                        loadPolicies()
                    } else {
                        showAlert("Xatolik: " + data.error, "error")
                    }
                })
                .catch((error) => showAlert("Xatolik: " + error.message, "error"))
                .finally(() => {
                    submitBtn.innerHTML = originalText
                    submitBtn.disabled = false
                })
        })
    }

    // Edit Policy Form
    const editPolicyForm = document.getElementById("editPolicyForm")
    if (editPolicyForm) {
        editPolicyForm.addEventListener("submit", function (e) {
            e.preventDefault()

            // Sync Quill content first
            syncAllQuillEditors()

            const formData = new FormData(this)
            const policyId = formData.get("policy_id")

            const submitBtn =
                document.querySelector('#editPolicyModal button[type="submit"]') ||
                document.querySelector("#editPolicyModal .btn-primary:last-child")

            if (!submitBtn) {
                console.error("Submit button not found for edit policy form")
                return
            }

            const originalText = submitBtn.innerHTML
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...'
            submitBtn.disabled = true

            fetch(`/admin/journals/${JOURNAL_ID}/policies/${policyId}/update/`, {
                method: "POST",
                body: formData,
                headers: {"X-CSRFToken": getCSRFToken()},
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        showAlert("Siyosat muvaffaqiyatli yangilandi!", "success")
                        if (typeof bootstrap !== "undefined") {
                            bootstrap.Modal.getInstance(document.getElementById("editPolicyModal")).hide()
                        }
                        loadPolicies()
                    } else {
                        showAlert("Xatolik: " + data.error, "error")
                    }
                })
                .catch((error) => showAlert("Xatolik: " + error.message, "error"))
                .finally(() => {
                    submitBtn.innerHTML = originalText
                    submitBtn.disabled = false
                })
        })
    }

    // Journal Settings Form
    const journalSettingsForm = document.getElementById("journalSettingsForm")
    if (journalSettingsForm) {
        journalSettingsForm.addEventListener("submit", function (e) {
            e.preventDefault()

            // Sync Quill content first
            syncAllQuillEditors()

            const formData = new FormData(this)

            const submitBtn = this.querySelector('button[type="submit"]')
            if (!submitBtn) {
                console.error("Submit button not found for journal settings form")
                return
            }

            const originalText = submitBtn.innerHTML
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...'
            submitBtn.disabled = true

            fetch(`/admin/journals/${JOURNAL_ID}/settings/`, {
                method: "POST",
                body: formData,
                headers: {"X-CSRFToken": getCSRFToken()},
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        showAlert("Jurnal sozlamalari saqlandi!", "success")
                        // Update page title if journal name changed
                        const newTitle = formData.get("title")
                        if (newTitle) {
                            document.title = `${newTitle} - Boshqaruv | Imfaktor Admin`
                            const h1 = document.querySelector("h1")
                            if (h1) h1.textContent = `${newTitle} - Boshqaruv`
                        }
                    } else {
                        showAlert("Xatolik: " + data.error, "error")
                    }
                })
                .catch((error) => showAlert("Xatolik: " + error.message, "error"))
                .finally(() => {
                    submitBtn.innerHTML = originalText
                    submitBtn.disabled = false
                })
        })
    }

    setupEditForms()
}

// Setup event listeners
function setupEventListeners() {
    // Author management
    document.getElementById("add-author").addEventListener("click", addAuthorRow)
    const addAuthorEditBtn = document.getElementById("add-author-edit")
    if (addAuthorEditBtn) {
        addAuthorEditBtn.addEventListener("click", addAuthorRowEdit)
    }

    const existingAuthorSelect = document.getElementById('existing_author_select');
    if (existingAuthorSelect) {
        existingAuthorSelect.addEventListener('change', function () {
            const selectedValue = this.value;
            if (!selectedValue) return
            try {
                const authorData = JSON.parse(selectedValue);
                const container = document.getElementById("authors-container");
                const authorRow = createAuthorRow(authorData);
                container.appendChild(authorRow);

                // Force DOM reflow
                authorRow.offsetHeight;

                // Update buttons BEFORE validation runs
                updateRemoveButtons();

                // Clear the select
                this.selectedIndex = 0;

            } catch (e) {
                console.error('Invalid author data:', e);
                showAlert('Xatolik: Muallif ma\'lumotlari noto\'g\'ri', 'error');
            }
        });
    }

    // Search functionality
    const articleSearch = document.getElementById("article-search")
    if (articleSearch) {
        articleSearch.addEventListener(
            "input",
            debounce(() => loadArticles(1), 300),
        )
    }

    const clearSearch = document.getElementById("clear-article-search")
    if (clearSearch) {
        clearSearch.addEventListener("click", () => {
            articleSearch.value = ""
            loadArticles(1)
        })
    }

    // Filter functionality
    const issueFilter = document.getElementById("article-issue-filter")
    if (issueFilter) {
        issueFilter.addEventListener("change", () => loadArticles(1))
    }

    const statusFilter = document.getElementById("article-status-filter")
    if (statusFilter) {
        statusFilter.addEventListener("change", () => loadArticles(1))
    }

    // Delete confirmation
    const confirmDeleteBtn = document.getElementById("confirmDeleteBtn")
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener("click", () => {
            if (deleteCallback) {
                deleteCallback()
                deleteCallback = null
                if (typeof bootstrap !== "undefined") {
                    bootstrap.Modal.getInstance(document.getElementById("deleteConfirmModal")).hide()
                }
            }
        })
    }

    // Tab switching
    document.querySelectorAll('#journalTabs button[data-bs-toggle="tab"]').forEach((tab) => {
        tab.addEventListener("shown.bs.tab", (event) => {
            const target = event.target.getAttribute("data-bs-target")
            if (target === "#issues-content") {
                loadIssues()
            } else if (target === "#articles-content") {
                loadArticles()
            } else if (target === "#editors-content") {
                loadEditors()
            } else if (target === "#policies-content") {
                loadPolicies()
            }
        })
    })
}

// Author management functions
function addAuthorRow() {
    const container = document.getElementById("authors-container")
    const authorRow = createAuthorRow()
    container.appendChild(authorRow)
    updateRemoveButtons()
}

function addAuthorRowEdit() {
    const container = document.getElementById("edit-authors-container")
    const authorRow = createAuthorRow()
    container.appendChild(authorRow)
    updateRemoveButtonsEdit()
}

function updateRemoveButtonsEdit() {
    const container = document.getElementById("edit-authors-container")
    if (container) {
        const removeButtons = container.querySelectorAll(".remove-author")
        removeButtons.forEach((btn) => {
            btn.style.display = container.children.length > 1 ? "block" : "none"
        })
    }
}

function createAuthorRow(author = null) {
    const row = document.createElement("div")
    row.className = "author-row mb-3 border rounded p-3"
    // Ensure first_name and last_name are marked as required, even for pre-filled authors
    row.innerHTML = `
        <div class="row g-2">
            <div class="col-md-3">
                <input type="text" class="form-control" name="author_first_name[]" placeholder="Ism *" required value="${author?.first_name || ""}">
            </div>
            <div class="col-md-3">
                <input type="text" class="form-control" name="author_middle_name[]" placeholder="Sharif" value="${author?.middle_name || ""}">
            </div>
            <div class="col-md-3">
                <input type="text" class="form-control" name="author_last_name[]" placeholder="Familiya *" required value="${author?.last_name || ""}">
            </div>
            <div class="col-md-3">
                <button type="button" class="btn btn-danger btn-sm remove-author">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
        <div class="row g-2 mt-2">
            <div class="col-md-4">
                <input type="email" class="form-control" name="author_email[]" placeholder="Email" value="${author?.email || ""}">
            </div>
            <div class="col-md-4">
                <input type="text" class="form-control" name="author_affiliation[]" placeholder="Tashkilot" value="${author?.affiliation || ""}">
            </div>
            <div class="col-md-4">
                <input type="text" class="form-control" name="author_orcid[]" placeholder="ORCID ID" value="${author?.orcid || ""}">
            </div>
        </div>
    `
    row.querySelector(".remove-author").addEventListener("click", () => {
        row.remove()
        if (row.parentElement && row.parentElement.id === "edit-authors-container") {
            updateRemoveButtonsEdit()
        } else {
            updateRemoveButtons()
        }
    })
    return row
}

function updateRemoveButtons() {
    const container = document.getElementById("authors-container")
    if (container) {
        const removeButtons = container.querySelectorAll(".remove-author")
        removeButtons.forEach((btn) => {
            btn.style.display = container.children.length > 1 ? "block" : "none"
        })
    }
}

// ===============================
// ISSUE CRUD OPERATIONS
// ===============================
function viewIssue(issueId) {
    // Open issue in new tab
    window.open(`/issues/${issueId}/`, "_blank")
}

function editIssue(issueId) {
    fetch(`/admin/issues/update/${issueId}/`, {
        method: "GET",
        headers: {"X-CSRFToken": getCSRFToken()},
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                const issue = data.issue
                const form = document.getElementById("editIssueForm")
                if (!form) {
                    showAlert("Edit form topilmadi", "error")
                    return
                }

                // Populate form fields
                const issueIdField = form.querySelector('[name="issue_id"]')
                const volumeField = form.querySelector('[name="volume"]')
                const numberField = form.querySelector('[name="number"]')
                const yearField = form.querySelector('[name="year"]')
                const titleField = form.querySelector('[name="title"]')
                const descriptionField = form.querySelector('[name="description"]')
                const dateField = form.querySelector('[name="date_published"]')
                const publishedField = form.querySelector('[name="is_published"]')

                if (issueIdField) issueIdField.value = issue.id
                if (volumeField) volumeField.value = issue.volume || ""
                if (numberField) numberField.value = issue.number || ""
                if (yearField) yearField.value = issue.year || ""
                if (titleField) titleField.value = issue.title || ""
                if (dateField) dateField.value = issue.date_published || ""
                if (publishedField) publishedField.checked = !!issue.is_published

                // Set Quill editor content and sync with textarea
                if (quillEditors.editIssueDescription && issue.description) {
                    quillEditors.editIssueDescription.root.innerHTML = issue.description
                }
                if (descriptionField) descriptionField.value = issue.description || ""

                // Show cover info if exists
                const coverInfo = document.getElementById("current-cover-info")
                if (coverInfo) {
                    coverInfo.style.display = issue.has_cover ? "block" : "none"
                }

                // Show modal
                if (typeof bootstrap !== "undefined") {
                    const modal = new bootstrap.Modal(document.getElementById("editIssueModal"))
                    modal.show()
                } else {
                    console.error("Bootstrap not available")
                    showAlert("Xatolik: Bootstrap yuklanmagan", "error")
                }
            } else {
                showAlert("Son ma'lumotlarini olishda xatolik: " + (data.error || "Noma'lum xatolik"), "error")
            }
        })
        .catch((error) => {
            console.error("Error editing issue:", error)
            showAlert("Xatolik: " + error.message, "error")
        })
}

function deleteIssue(issueId) {
    showDeleteConfirmation("Son", () => {
        fetch(`/admin/issues/delete/${issueId}/`, {
            method: "POST",
            headers: {"X-CSRFToken": getCSRFToken()},
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    showAlert("Son muvaffaqiyatli o'chirildi!", "success")
                    loadIssues() // Reload issues list
                    loadArticles() // Reload articles to update counts
                } else {
                    showAlert("Xatolik: " + (data.error || "Noma'lum xatolik"), "error")
                }
            })
            .catch((error) => {
                console.error("Error deleting issue:", error)
                showAlert("Xatolik: " + error.message, "error")
            })
    })
}

function viewArticle(articleId) {
    window.open(`/articles/${articleId}/`, "_blank")
}

function editArticle(articleId) {
    fetch(`/admin/articles/update/${articleId}/`)
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                const article = data.article
                const form = document.getElementById("editArticleForm")

                // Hidden id
                form.querySelector('[name="article_id"]').value = article.id

                // Sarlavha va boshqalar
                form.querySelector('[name="title"]').value = article.title || ""
                form.querySelector('[name="subtitle"]').value = article.subtitle || ""
                form.querySelector('[name="keywords"]').value = article.keywords || ""
                form.querySelector('[name="meta_description"]').value = article.meta_description || ""
                form.querySelector('[name="doi"]').value = article.doi || ""
                form.querySelector('[name="language"]').value = article.language || ""
                form.querySelector('[name="featured"]').checked = !!article.featured
                form.querySelector('[name="open_access"]').checked = !!article.open_access
                form.querySelector('[name="is_published"]').checked = !!article.is_published
                form.querySelector('[name="date_published"]').value = article.date_published || ""
                form.querySelector('[name="first_page"]').value = article.first_page || ""
                form.querySelector('[name="last_page"]').value = article.last_page || ""
                form.querySelector('[name="journal"]').value = article.journal_id || ""

                // ✅ Abstract
                if (quillEditors.editArticleAbstract && article.abstract) {
                    quillEditors.editArticleAbstract.root.innerHTML = article.abstract
                }
                const absTextarea = form.querySelector('[name="abstract"]')
                if (absTextarea) absTextarea.value = article.abstract || ""

                // ✅ References
                if (quillEditors.editArticleReferences && article.references) {
                    quillEditors.editArticleReferences.root.innerHTML = article.references
                }
                const refTextarea = form.querySelector('[name="references"]')
                if (refTextarea) refTextarea.value = article.references || ""

                // Authors
                const authorsContainer = document.getElementById("edit-authors-container")
                authorsContainer.innerHTML = ""
                ;(article.authors || []).forEach((author) => {
                    const row = createAuthorRow(author)
                    authorsContainer.appendChild(row)
                })

                // Show modal
                if (typeof bootstrap !== "undefined") {
                    new bootstrap.Modal(document.getElementById("editArticleModal")).show()
                }
            } else {
                showAlert("Maqola ma'lumotlarini olishda xatolik: " + (data.error || "Noma'lum xatolik"), "error")
            }
        })
        .catch((error) => showAlert("Xatolik: " + error.message, "error"))
}


function deleteArticle(articleId) {
    showDeleteConfirmation("Maqola", () => {
        fetch(`/admin/articles/delete/${articleId}/`, {
            method: "POST",
            headers: {"X-CSRFToken": getCSRFToken()},
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    showAlert("Maqola muvaffaqiyatli o'chirildi!", "success")
                    loadArticles() // Reload articles table/list
                } else {
                    showAlert("Xatolik: " + (data.error || "Noma'lum xatolik"), "error")
                }
            })
            .catch((error) => {
                showAlert("Xatolik: " + error.message, "error")
            })
    })
}

function loadAuthorsForDropdown() {
    const authorSelect = document.getElementById('existing_author_select');
    if (!authorSelect) return

    // Clear existing options except the placeholder
    authorSelect.innerHTML = '<option value="">Muallifni izlash va tanlash...</option>'

    // Fetch authors from the API
    // Assuming you have an endpoint like '/admin/authors/list/' that returns JSON
    fetch('/admin/authors/list/')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.authors) {
                data.authors.forEach(author => {
                    const option = document.createElement('option');
                    option.value = JSON.stringify({
                        id: author.id,
                        first_name: author.first_name,
                        middle_name: author.middle_name,
                        last_name: author.last_name,
                        email: author.email,
                        affiliation: author.affiliation,
                        orcid: author.orcid
                    });
                    option.textContent = `${author.full_name} (${author.email})`;
                    authorSelect.appendChild(option);
                });
            } else {
                console.error('Failed to load authors for dropdown:', data.error);
            }
        })
        .catch(error => {
            console.error('Error loading authors for dropdown:', error);
        });
}

// ===============================
// EXPORT FUNCTIONS
// ===============================
// exportEditors and exportPolicies remain the same
function exportEditors() {
    window.open(`/admin/journals/${JOURNAL_ID}/export/editors/`, "_blank")
}

function exportPolicies() {
    window.open(`/admin/journals/${JOURNAL_ID}/export/policies/`, "_blank")
}

// ===============================
// UTILITY FUNCTIONS
// ===============================
function showDeleteConfirmation(entityName, callback) {
    const deleteConfirmMessage = document.getElementById("deleteConfirmMessage")
    if (deleteConfirmMessage) {
        deleteConfirmMessage.textContent = `${entityName}ni o'chirishni xohlaysizmi? Bu amalni ortga qaytarib bo'lmaydi.`
    }
    deleteCallback = callback
    if (typeof bootstrap !== "undefined") {
        new bootstrap.Modal(document.getElementById("deleteConfirmModal")).show()
    } else {
        console.error("Bootstrap not available")
        showAlert("Xatolik: Bootstrap yuklanmagan", "error")
    }
}

function showAlert(message, type = "info") {
    const alertDiv = document.createElement("div")
    alertDiv.className = `alert alert-${type === "error" ? "danger" : type} alert-dismissible fade show position-fixed`
    alertDiv.style.cssText = "top: 20px; right: 20px; z-index: 9999; min-width: 300px;"

    const iconMap = {
        success: "check-circle",
        error: "exclamation-triangle",
        warning: "exclamation-triangle",
        info: "info-circle",
    }

    alertDiv.innerHTML = `
        <i class="fas fa-${iconMap[type] || "info-circle"} me-2"></i>
        ${escapeHtml(message)}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `

    document.body.appendChild(alertDiv)

    setTimeout(() => {
        if (typeof bootstrap !== "undefined") {
            const alert = bootstrap.Alert.getOrCreateInstance(alertDiv)
            if (alert) alert.close()
        } else {
            alertDiv.remove()
        }
    }, 5000)
}

function updatePagination(type, pagination) {
    const paginationEl = document.getElementById(`${type}-pagination`)
    if (!paginationEl || !pagination) return

    let html = ""

    if (pagination.has_previous) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="load${capitalize(type)}(${pagination.current - 1}); return false;"><i class="fas fa-chevron-left"></i></a></li>`
    }

    for (let i = 1; i <= pagination.total_pages; i++) {
        if (i === pagination.current) {
            html += `<li class="page-item active"><span class="page-link">${i}</span></li>`
        } else if (
            i === 1 ||
            i === pagination.total_pages ||
            (i >= pagination.current - 2 && i <= pagination.current + 2)
        ) {
            html += `<li class="page-item"><a class="page-link" href="#" onclick="load${capitalize(type)}(${i}); return false;">${i}</a></li>`
        } else if (i === pagination.current - 3 || i === pagination.current + 3) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`
        }
    }

    if (pagination.has_next) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="load${capitalize(type)}(${pagination.current + 1}); return false;"><i class="fas fa-chevron-right"></i></a></li>`
    }

    paginationEl.innerHTML = html
}

function getCSRFToken() {
    const name = "csrftoken"
    let cookieValue = null
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";")
        for (let cookie of cookies) {
            cookie = cookie.trim()
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
                break
            }
        }
    }
    return cookieValue
}

function escapeHtml(text) {
    if (!text) return ""
    const map = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"}
    return text.toString().replace(/[&<>"']/g, (m) => map[m])
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1)
}

function debounce(func, wait) {
    let timeout
    return function (...args) {
        clearTimeout(timeout)
        timeout = setTimeout(() => func.apply(this, args), wait)
    }
}

// Clear forms on modal hide
const addArticleModal = document.getElementById("addArticleModal")
if (addArticleModal) {
    addArticleModal.addEventListener("hidden.bs.modal", () => {
        const form = document.getElementById("addArticleForm")
        if (form) form.reset()

        const authorsContainer = document.getElementById("authors-container")
        if (authorsContainer) {
            authorsContainer.innerHTML = `
            <div class="author-row mb-3 border rounded p-3">
                <div class="row g-2">
                    <div class="col-md-3">
                        <input type="text" class="form-control" name="author_first_name[]" placeholder="Ism *" required>
                    </div>
                    <div class="col-md-3">
                        <input type="text" class="form-control" name="author_middle_name[]" placeholder="Sharif">
                    </div>
                    <div class="col-md-3">
                        <input type="text" class="form-control" name="author_last_name[]" placeholder="Familiya *" required>
                    </div>
                    <div class="col-md-3">
                        <button type="button" class="btn btn-danger btn-sm remove-author">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="row g-2 mt-2">
                    <div class="col-md-4">
                        <input type="email" class="form-control" name="author_email[]" placeholder="Email">
                    </div>
                    <div class="col-md-4">
                        <input type="text" class="form-control" name="author_affiliation[]" placeholder="Tashkilot">
                    </div>
                    <div class="col-md-4">
                        <input type="text" class="form-control" name="author_orcid[]" placeholder="ORCID ID">
                    </div>
                </div>
            </div>
        `
        }
        hideFileInfo()
        updateRemoveButtons()
        // Clear Quill editor
        if (quillEditors.articleAbstract) {
            quillEditors.articleAbstract.setContents([])
        }
    })
}

const addIssueModal = document.getElementById("addIssueModal")
if (addIssueModal) {
    addIssueModal.addEventListener("hidden.bs.modal", () => {
        const form = document.getElementById("addIssueForm")
        if (form) form.reset()

        const currentYear = new Date().getFullYear()
        const issueYear = document.getElementById("issue_year")
        if (issueYear) issueYear.value = currentYear

        // Clear Quill editor
        if (quillEditors.issueDescription) {
            quillEditors.issueDescription.setContents([])
        }
    })
}

const addEditorModal = document.getElementById("addEditorModal")
if (addEditorModal) {
    addEditorModal.addEventListener("hidden.bs.modal", () => {
        const form = document.getElementById("addEditorForm")
        if (form) form.reset()
    })
}

const addPolicyModal = document.getElementById("addPolicyModal")
if (addPolicyModal) {
    addPolicyModal.addEventListener("hidden.bs.modal", () => {
        const form = document.getElementById("addPolicyForm")
        if (form) form.reset()

        const policyDate = document.getElementById("policy_effective_date")
        if (policyDate) policyDate.value = new Date().toISOString().split("T")[0]

        // Clear Quill editors
        if (quillEditors.addPolicyShortDescription) quillEditors.addPolicyShortDescription.setContents([])
        if (quillEditors.addPolicyContent) quillEditors.addPolicyContent.setContents([])
        if (quillEditors.addPolicyRequirements) quillEditors.addPolicyRequirements.setContents([])
        if (quillEditors.addPolicyExamples) quillEditors.addPolicyExamples.setContents([])
    })
}

// Call this when showing the add article modal:
const addArticleModalShow = document.getElementById("addArticleModal")
if (addArticleModalShow) {
    addArticleModalShow.addEventListener("show.bs.modal", setActiveIssueInfo)
}