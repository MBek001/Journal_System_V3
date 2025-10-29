// admin.js - Imfaktor Admin Panel JavaScript (100% Fixed & Enhanced Version)
// Global variables
let currentPage = 1;
let currentSection = "dashboard";
let deleteCallback = null;
const quillEditors = {};
const Quill = window.Quill;
const bootstrap = window.bootstrap;

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
    initializeAdminPanel();
});

// ## INITIALIZATION SECTION ##
function initializeAdminPanel() {
    setupNavigation();
    setupFileUpload();
    setupAuthorFormHandlers();
    setupFormHandlers();
    setupFilters();
    loadInitialData();
    setupMobileMenu();
    setupModals();
    initializeQuillEditors();
    // Load utilities data after initialization
    loadFanTarmoqs();
    loadIlmiyNashrs();
    loadNavigations(); // NEW: Load Navigation data
}

// ## QUILL EDITOR INITIALIZATION ##
function initializeQuillEditors() {
    // Initialize Quill editors for different forms
    const editorConfigs = [
        {container: "#journal-description-editor", input: "#journal-description-input"},
        {container: "#edit-journal-description-editor", input: "#edit-journal-description-input"},
        {container: "#author-bio-editor", input: "#author-bio-input"},
        {container: "#edit-author-bio-editor", input: "#edit-author-bio-input"},
    ];

    editorConfigs.forEach((config) => {
        const container = document.querySelector(config.container);
        if (container) {
            const quill = new Quill(config.container, {
                theme: "snow",
                modules: {
                    toolbar: [
                        [{header: [1, 2, 3, false]}],
                        ["bold", "italic", "underline", "strike"],
                        [{list: "ordered"}, {list: "bullet"}],
                        [{script: "sub"}, {script: "super"}],
                        ["link", "blockquote"],
                        ["clean"],
                    ],
                },
                placeholder: "Matnni kiriting...",
            });
            // Store editor reference
            quillEditors[config.container] = quill;
            // Update hidden input when content changes
            quill.on("text-change", () => {
                const input = document.querySelector(config.input);
                if (input) {
                    input.value = quill.root.innerHTML;
                }
            });
        }
    });
}

function getQuillContent(editorId) {
    const editor = quillEditors[editorId];
    return editor ? editor.root.innerHTML : "";
}

function setQuillContent(editorId, content) {
    const editor = quillEditors[editorId];
    if (editor) {
        editor.root.innerHTML = content || "";
    }
}

// ## NAVIGATION SECTION ##
function setupNavigation() {
    const navLinks = document.querySelectorAll(".nav-link[data-section]");
    const sections = document.querySelectorAll(".section-content");
    const quickActionBtns = document.querySelectorAll("button[data-section]");

    function showSection(sectionId) {
        sections.forEach((section) => (section.style.display = "none"));
        const targetSection = document.getElementById("section-" + sectionId);
        if (targetSection) {
            targetSection.style.display = "block";
            currentSection = sectionId;
        }
        navLinks.forEach((link) => link.classList.remove("active"));
        const activeLink = document.querySelector(`[data-section="${sectionId}"]`);
        if (activeLink && activeLink.classList.contains("nav-link")) {
            activeLink.classList.add("active");
        }
        if (window.innerWidth <= 991) {
            const sidebar = document.querySelector(".sidebar");
            if (sidebar) sidebar.classList.remove("show");
        }
        loadSectionData(sectionId);
    }

    navLinks.forEach((link) => {
        link.addEventListener("click", function (e) {
            e.preventDefault();
            showSection(this.getAttribute("data-section"));
        });
    });

    quickActionBtns.forEach((btn) => {
        btn.addEventListener("click", function () {
            showSection(this.getAttribute("data-section"));
        });
    });
}

function loadSectionData(sectionId) {
    switch (sectionId) {
        case "journals":
            loadJournals();
            break;
        case "authors":
            loadAuthors();
            break;
        case "seo":
            loadSEO();
            break;
        case "utilities":
            loadFanTarmoqs();
            loadIlmiyNashrs();
            loadNavigations();
            break;
        default:
            break;
    }
}

// ## FILE UPLOAD SECTION (Generic) ##
function setupFileUpload() {
    console.log("File upload utilities initialized.");
}

// ## AUTHOR MANAGEMENT SECTION ##
function setupAuthorFormHandlers() {
    // Add Author Form
    const addAuthorForm = document.getElementById("addAuthorForm");
    if (addAuthorForm) {
        addAuthorForm.addEventListener("submit", function (e) {
            e.preventDefault();
            // Update bio from Quill editor
            const bioContent = getQuillContent("#author-bio-editor");
            document.getElementById("author-bio-input").value = bioContent;

            const formData = new FormData(this);

            showLoadingIndicator("addAuthorForm");
            setTimeout(() => {
                fetch("/admin/authors/add/", {
                    method: "POST",
                    body: formData,
                    headers: {"X-CSRFToken": getCSRFToken()},
                })
                    .then((response) => response.json())
                    .then((data) => {
                        hideLoadingIndicator("addAuthorForm");
                        if (data.success) {
                            showAlert("Muallif muvaffaqiyatli qo'shildi!", "success");
                            this.reset();
                            setQuillContent("#author-bio-editor", "");
                            const modal = bootstrap.Modal.getInstance(document.getElementById("addAuthorModal"));
                            modal.hide();
                            loadAuthors(currentPage);
                        } else {
                            showAlert("Xatolik: " + (data.error || "Noma'lum xatolik"), "error");
                        }
                    })
                    .catch((error) => {
                        hideLoadingIndicator("addAuthorForm");
                        showAlert("Xatolik: " + error.message, "error");
                    });
            }, 500);
        });
    }

    // Edit Author Form
    const editAuthorForm = document.getElementById("editAuthorForm");
    if (editAuthorForm) {
        editAuthorForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const bioContent = getQuillContent("#edit-author-bio-editor");
            document.getElementById("edit-author-bio-input").value = bioContent;

            const formData = new FormData(this);
            const authorId = formData.get("author_id");

            showLoadingIndicator("editAuthorForm");
            setTimeout(() => {
                fetch(`/admin/authors/update/${authorId}/`, {
                    method: "POST",
                    body: formData,
                    headers: {"X-CSRFToken": getCSRFToken()},
                })
                    .then((response) => response.json())
                    .then((data) => {
                        hideLoadingIndicator("editAuthorForm");
                        if (data.success) {
                            showAlert("Muallif ma'lumotlari yangilandi!", "success");
                            const modal = bootstrap.Modal.getInstance(document.getElementById("editAuthorModal"));
                            modal.hide();
                            loadAuthors(currentPage);
                        } else {
                            showAlert("Xatolik: " + (data.error || "Noma'lum xatolik"), "error");
                        }
                    })
                    .catch((error) => {
                        hideLoadingIndicator("editAuthorForm");
                        showAlert("Xatolik: " + error.message, "error");
                    });
            }, 500);
        });
    }

    // Search functionality
    const authorSearch = document.getElementById("author-search");
    if (authorSearch) {
        authorSearch.addEventListener(
            "input",
            debounce(function () {
                loadAuthors(1, this.value);
            }, 300)
        );
    }

    // Clear search
    const clearSearchBtn = document.getElementById("clear-search");
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener("click", () => {
            const searchInput = document.getElementById("author-search");
            if (searchInput) {
                searchInput.value = "";
                loadAuthors(1);
            }
        });
    }
}

function showLoadingIndicator(formId) {
    const form = document.getElementById(formId);
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...';
        submitBtn.disabled = true;
    }
}

function hideLoadingIndicator(formId) {
    const form = document.getElementById(formId);
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.innerHTML = '<i class="fas fa-save me-2"></i>Saqlash';
        submitBtn.disabled = false;
    }
}

function loadAuthors(page = 1, search = "") {
    currentPage = page;
    let url = `/admin/authors/list/?page=${page}`;
    if (search) {
        url += `&search=${encodeURIComponent(search)}`;
    }

    const loadingDiv = document.getElementById("authors-loading");
    if (loadingDiv) loadingDiv.style.display = "block";

    fetch(url)
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                updateAuthorTable(data.authors || []);
                updatePagination("authors", data.pagination);
                updateAuthorsPaginationInfo(data.pagination);
            } else {
                showAlert("Mualliflarni yuklashda xatolik: " + (data.error || "Noma'lum xatolik"), "error");
            }
        })
        .catch((error) => showAlert("Server bilan bog'lanishda xatolik: " + error.message, "error"))
        .finally(() => {
            if (loadingDiv) loadingDiv.style.display = "none";
        });
}

function updateAuthorTable(authors) {
    const tbody = document.querySelector("#authors-table-body");
    if (!tbody) return;

    tbody.innerHTML = "";

    if (!authors || authors.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Mualliflar topilmadi</td></tr>';
        return;
    }

    authors.forEach((author) => {
        const row = document.createElement("tr");
        const hasPhoto = author.has_photo;
        const photoHtml = hasPhoto
            ? `<img src="${author.photo_url}" alt="${escapeHtml(author.full_name)}" class="author-photo-preview rounded">`
            : `<div class="bg-light rounded p-2" style="width: 50px; height: 50px;"><i class="fas fa-user text-muted"></i></div>`;

        row.innerHTML = `
            <td class="text-center">${photoHtml}</td>
            <td>${escapeHtml(author.full_name)}</td>
            <td>
                ${author.email ? `<div>${escapeHtml(author.email)}</div>` : ""}
                ${author.orcid ? `<div class="small text-muted">ORCID: ${escapeHtml(author.orcid)}</div>` : ""}
            </td>
            <td>${escapeHtml(author.affiliation || "Kiritilmagan")}</td>
            <td><span class="badge bg-info">${author.article_count}</span></td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-sm btn-success send-email" data-id="${author.id}" title="Email Jo'natish" ${!author.email ? 'disabled' : ''}>
                        <i class="fas fa-envelope"></i>
                    </button>
                    <button class="btn btn-sm btn-info view-author" data-id="${author.id}" title="Ko'rish">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-primary edit-author" data-id="${author.id}" title="Tahrirlash">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger delete-author" data-id="${author.id}" title="O'chirish">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });

    // Attach event listeners
    document.querySelectorAll(".send-email").forEach((btn) => {
        btn.addEventListener("click", () => {
            const emailUrl = `/admin/message-authors/${btn.dataset.id}/`;
            window.open(emailUrl, "_blank");
        });
    });

    document.querySelectorAll(".view-author").forEach((btn) => {
        btn.addEventListener("click", () => viewAuthor(btn.dataset.id));
    });

    document.querySelectorAll(".edit-author").forEach((btn) => {
        btn.addEventListener("click", () => editAuthor(btn.dataset.id));
    });

    document.querySelectorAll(".delete-author").forEach((btn) => {
        btn.addEventListener("click", () => deleteAuthor(btn.dataset.id));
    });
}

function updateAuthorsPaginationInfo(pagination) {
    const resultsInfo = document.getElementById("authors-results-info");
    const paginationContainer = document.getElementById("authors-pagination-container");
    const noResultsMsg = document.getElementById("no-authors-message");
    const loadingDiv = document.getElementById("authors-loading");

    if (pagination.total_count === 0) {
        if (noResultsMsg) noResultsMsg.style.display = "block";
        if (paginationContainer) paginationContainer.style.display = "none";
        if (resultsInfo) resultsInfo.textContent = "";
    } else {
        if (noResultsMsg) noResultsMsg.style.display = "none";
        if (paginationContainer) paginationContainer.style.display = "block";
        if (resultsInfo) {
            const start = (pagination.current - 1) * 20 + 1;
            const end = Math.min(pagination.current * 20, pagination.total_count);
            resultsInfo.textContent = `${start}-${end} / ${pagination.total_count} natija`;
        }
    }
}

function viewAuthor(authorId) {
    fetch(`/admin/authors/details/${authorId}/`)
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                const author = data.author;
                const modalContent = document.getElementById("viewAuthorContent");
                let articlesHtml = "";

                if (author.recent_articles && author.recent_articles.length > 0) {
                    articlesHtml = `
                        <h6 class="mt-3">So'nggi maqolalar:</h6>
                        <ul class="list-unstyled">
                            ${author.recent_articles
                        .map(
                            (article) => `
                                <li class="mb-2">
                                    <a href="/articles/${article.slug}/" target="_blank" class="text-decoration-none">
                                        <i class="fas fa-file-alt me-2"></i>${escapeHtml(article.title)}
                                    </a>
                                    <br><small class="text-muted">${escapeHtml(article.journal)} - ${article.date}</small>
                                </li>
                            `
                        )
                        .join("")}
                        </ul>
                    `;
                } else {
                    articlesHtml = '<p class="text-muted">Hozircha maqola yo\'q</p>';
                }

                modalContent.innerHTML = `
                    <div class="row">
                        <div class="col-md-4 text-center">
                            ${
                    author.has_photo
                        ? `<img src="${author.photo_url}" alt="${escapeHtml(author.full_name)}" class="img-fluid rounded mb-3" style="max-height: 200px;">`
                        : '<div class="bg-light rounded p-5 mb-3"><i class="fas fa-user fa-3x text-muted"></i></div>'
                }
                            <h5>${escapeHtml(author.full_name)}</h5>
                            <p class="text-muted">${author.is_active ? '<span class="badge bg-success">Faol</span>' : '<span class="badge bg-secondary">Nofaol</span>'}</p>
                        </div>
                        <div class="col-md-8">
                            <table class="table table-sm">
                                <tr><th width="40%">Email:</th><td>${escapeHtml(author.email || "Kiritilmagan")}</td></tr>
                                <tr><th>Tashkilot:</th><td>${escapeHtml(author.affiliation || "Kiritilmagan")}</td></tr>
                                <tr><th>Bo'lim:</th><td>${escapeHtml(author.department || "Kiritilmagan")}</td></tr>
                                <tr><th>Lavozim:</th><td>${escapeHtml(author.position || "Kiritilmagan")}</td></tr>
                                <tr><th>Ilmiy unvon:</th><td>${escapeHtml(author.academic_title || "Kiritilmagan")}</td></tr>
                                <tr><th>Ilmiy daraja:</th><td>${escapeHtml(author.academic_degree || "Kiritilmagan")}</td></tr>
                                <tr><th>ORCID:</th><td>${author.orcid ? `<a href="https://orcid.org/${author.orcid}" target="_blank">${escapeHtml(author.orcid)}</a>` : "Kiritilmagan"}</td></tr>
                                <tr><th>Google Scholar:</th><td>${author.google_scholar_id ? `<a href="https://scholar.google.com/citations?user=${author.google_scholar_id}" target="_blank">${escapeHtml(author.google_scholar_id)}</a>` : "Kiritilmagan"}</td></tr>
                                <tr><th>Veb-sayt:</th><td>${author.website ? `<a href="${escapeHtml(author.website)}" target="_blank">${escapeHtml(author.website)}</a>` : "Kiritilmagan"}</td></tr>
                                <tr><th>Maqolalar soni:</th><td><span class="badge bg-info">${author.article_count}</span></td></tr>
                            </table>
                            ${author.bio ? `<div class="mt-3"><h6>Biografiya:</h6><div>${author.bio}</div></div>` : ""}
                            ${articlesHtml}
                        </div>
                    </div>
                `;

                const modal = new bootstrap.Modal(document.getElementById("viewAuthorModal"));
                modal.show();
            } else {
                showAlert("Muallif ma'lumotlarini olishda xatolik", "error");
            }
        })
        .catch((error) => showAlert("Xatolik: " + error.message, "error"));
}

function editAuthor(authorId) {
    fetch(`/admin/authors/update/${authorId}/`)
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                const author = data.author;
                const form = document.getElementById("editAuthorForm");
                if (!form) return;

                // Fill form fields
                form.querySelector('[name="author_id"]').value = author.id;
                form.querySelector('[name="first_name"]').value = author.first_name || "";
                form.querySelector('[name="middle_name"]').value = author.middle_name || "";
                form.querySelector('[name="last_name"]').value = author.last_name || "";
                form.querySelector('[name="email"]').value = author.email || "";
                form.querySelector('[name="affiliation"]').value = author.affiliation || "";
                form.querySelector('[name="department"]').value = author.department || "";
                form.querySelector('[name="position"]').value = author.position || "";
                form.querySelector('[name="academic_title"]').value = author.academic_title || "";
                form.querySelector('[name="academic_degree"]').value = author.academic_degree || "";
                form.querySelector('[name="orcid"]').value = author.orcid || "";
                form.querySelector('[name="google_scholar_id"]').value = author.google_scholar_id || "";
                form.querySelector('[name="website"]').value = author.website || "";
                form.querySelector('[name="is_active"]').checked = author.is_active;

                setQuillContent("#edit-author-bio-editor", author.bio || "");

                const modal = new bootstrap.Modal(document.getElementById("editAuthorModal"));
                modal.show();
            } else {
                showAlert("Muallif ma'lumotlarini olishda xatolik: " + (data.error || "Noma'lum xatolik"), "error");
            }
        })
        .catch((error) => showAlert("Xatolik: " + error.message, "error"));
}

function deleteAuthor(authorId) {
    showDeleteConfirmation(
        "Muallif",
        `/admin/authors/delete/${authorId}/`,
        () => {
            const search = document.getElementById("author-search") ? document.getElementById("author-search").value : "";
            loadAuthors(currentPage, search);
        }
    );
}

function exportAuthors() {
    window.location.href = "/admin/export/authors/";
}


// ## JOURNALS SECTION ##
function setupJournalForm() {
    const addJournalForm = document.getElementById("addJournalForm");
    const editJournalForm = document.getElementById("editJournalForm");

    if (addJournalForm) {
        addJournalForm.addEventListener("submit", function (e) {
            e.preventDefault();
            // Update description from Quill editor
            const descriptionContent = getQuillContent("#journal-description-editor");
            document.getElementById("journal-description-input").value = descriptionContent;

            const formData = new FormData(this);
            if (!validateJournalForm(formData)) return;

            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...';
            submitBtn.disabled = true;

            fetch("/admin/journals/add/", {
                method: "POST",
                body: formData,
                headers: {"X-CSRFToken": getCSRFToken()},
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        showAlert("Jurnal muvaffaqiyatli qo'shildi!", "success");
                        this.reset();
                        setQuillContent("#journal-description-editor", "");
                        const modal = bootstrap.Modal.getInstance(document.getElementById("addJournalModal"));
                        if (modal) modal.hide();
                        loadJournals();
                        updateJournalSelects();
                    } else {
                        showAlert("Xatolik: " + (data.error || "Noma'lum xatolik"), "error");
                    }
                })
                .catch((error) => showAlert("Xatolik yuz berdi: " + error.message, "error"))
                .finally(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                });
        });
    }

    if (editJournalForm) {
        editJournalForm.addEventListener("submit", function (e) {
            e.preventDefault();
            // Update description from Quill editor
            const descriptionContent = getQuillContent("#edit-journal-description-editor");
            document.getElementById("edit-journal-description-input").value = descriptionContent;

            const formData = new FormData(this);
            const journalId = formData.get("journal_id");
            if (!validateJournalForm(formData)) return;

            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...';
            submitBtn.disabled = true;

            fetch(`/admin/journals/update/${journalId}/`, {
                method: "POST",
                body: formData,
                headers: {"X-CSRFToken": getCSRFToken()},
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        showAlert("Jurnal muvaffaqiyatli yangilandi!", "success");
                        const modal = bootstrap.Modal.getInstance(document.getElementById("editJournalModal"));
                        modal.hide();
                        loadJournals();
                        updateJournalSelects();
                    } else {
                        showAlert("Xatolik: " + (data.error || "Noma'lum xatolik"), "error");
                    }
                })
                .catch((error) => showAlert("Xatolik yuz berdi: " + error.message, "error"))
                .finally(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                });
        });
    }
}

function validateJournalForm(formData) {
    const title = formData.get("title");
    const url_slug = formData.get("url_slug");
    if (!title || title.trim().length < 3) {
        showAlert("Jurnal nomi kamida 3 belgidan iborat bo'lishi kerak", "warning");
        return false;
    }
    if (!url_slug || !/^[a-z0-9-]+$/.test(url_slug)) {
        showAlert("URL slug faqat kichik harflar, raqamlar va chiziqcha bo'lishi kerak", "warning");
        return false;
    }
    return true;
}

function loadJournals(page = currentPage) {
    fetch(`/admin/journals/list/?page=${page}`)
        .then((response) => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then((data) => {
            if (data.success) {
                updateJournalTable(data.journals || []);
                updatePagination("journals", data.pagination);
                currentPage = page;
            } else {
                showAlert("Jurnallarni yuklashda xatolik: " + (data.error || "Noma'lum xatolik"), "error");
                updateJournalTable([]);
            }
        })
        .catch((error) => {
            console.error("Error loading journals:", error);
            showAlert("Jurnallarni yuklashda xatolik: " + error.message, "error");
            updateJournalTable([]);
        });
}

function updateJournalTable(journals) {
    const tbody = document.querySelector("#journals-table-body");
    if (!tbody) return;

    tbody.innerHTML = "";

    if (!journals || journals.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">Jurnallar mavjud emas</td></tr>';
        return;
    }

    journals.forEach((journal) => {
        const row = document.createElement("tr");
        const issnDisplay = [];
        if (journal.issn_print) issnDisplay.push(`Print: ${journal.issn_print}`);
        if (journal.issn_online) issnDisplay.push(`Online: ${journal.issn_online}`);

        row.innerHTML = `
            <td>
                ${escapeHtml(journal.title)}
                ${journal.initials ? `<br><small class="text-muted">${escapeHtml(journal.initials)}</small>` : ""}
            </td>
            <td>${escapeHtml(journal.url_slug || "")}</td>
            <td>${issnDisplay.length > 0 ? `<small>${issnDisplay.join("<br>")}</small>` : "-"}</td>
            <td>${escapeHtml(journal.publisher || "-")}</td>
            <td><span class="badge bg-info">${journal.article_count || 0}</span></td>
            <td><span class="badge bg-primary">${journal.issue_count || 0}</span></td>
            <td>
                ${journal.is_active ? '<span class="badge bg-success">Faol</span>' : '<span class="badge bg-secondary">Nofaol</span>'}
                ${journal.is_open_access ? '<span class="badge bg-info ms-1">Open Access</span>' : ""}
            </td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-sm btn-success view-journal" data-id="${journal.id}" data-slug="${journal.url_slug}" title="Ko\'rish">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-primary edit-journal" data-id="${journal.id}" title="Tahrirlash">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger delete-journal" data-id="${journal.id}" title="O\'chirish">
                        <i class="fas fa-trash"></i>
                    </button>
                    <a href="/admin/journals/${journal.id}/manage/" class="btn btn-sm btn-warning" title="Batafsil Boshqaruv">
                        <i class="fas fa-cog"></i>
                    </a>
                    ${journal.website ? `<a href="${escapeHtml(journal.website)}" class="btn btn-sm btn-info" target="_blank" title="Veb-sayt"><i class="fas fa-external-link-alt"></i></a>` : ""}
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });

    document.querySelectorAll(".view-journal").forEach((btn) => {
        btn.addEventListener("click", () => viewJournal(btn.dataset.id, btn.dataset.slug));
    });

    document.querySelectorAll(".edit-journal").forEach((btn) => {
        btn.addEventListener("click", () => editJournal(btn.dataset.id));
    });

    document.querySelectorAll(".delete-journal").forEach((btn) => {
        btn.addEventListener("click", () => deleteJournal(btn.dataset.id));
    });
}

function viewJournal(journalId, journalSlug) {
    window.open(`/journals/${journalSlug}/`, "_blank");
}

function editJournal(journalId) {
    fetch(`/admin/journals/update/${journalId}/`)
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                const journal = data.journal;
                const form = document.getElementById("editJournalForm");
                form.querySelector('[name="journal_id"]').value = journal.id;
                form.querySelector('[name="title"]').value = journal.title || "";
                form.querySelector('[name="url_slug"]').value = journal.url_slug || "";
                form.querySelector('[name="issn_print"]').value = journal.issn_print || "";
                form.querySelector('[name="issn_online"]').value = journal.issn_online || "";
                form.querySelector('[name="publisher"]').value = journal.publisher || "";
                form.querySelector('[name="is_active"]').checked = !!journal.is_active;
                form.querySelector('[name="is_open_access"]').checked = !!journal.is_open_access;
                // Set Quill editor content
                setQuillContent("#edit-journal-description-editor", journal.description || "");

                const modal = new bootstrap.Modal(document.getElementById("editJournalModal"));
                modal.show();
            } else {
                showAlert("Jurnal ma'lumotlarini olishda xatolik: " + (data.error || "Noma'lum xatolik"), "error");
            }
        })
        .catch((error) => showAlert("Xatolik: " + error.message, "error"));
}

function deleteJournal(journalId) {
    showDeleteConfirmation("Jurnal", `/admin/journals/delete/${journalId}/`, loadJournals);
}

function exportJournals() {
    window.location.href = "/admin/export/journals/";
}

function updateJournalSelects() {
    fetch("/admin/journals/list/")
        .then((response) => response.json())
        .then((data) => {
            const selects = document.querySelectorAll('select[name="journal"]');
            selects.forEach((select) => {
                const currentValue = select.value;
                select.innerHTML = '<option value="">Jurnalni tanlang</option>';
                ;(data.journals || []).forEach((journal) => {
                    select.innerHTML += `<option value="${journal.id}">${escapeHtml(journal.title)}</option>`;
                });
                if (currentValue) select.value = currentValue;
            });
        })
        .catch((error) => showAlert("Jurnal ro'yxatini yangilashda xatolik: " + error.message, "error"));
}

// ## SEO SECTION ##
function setupSEOForm() {
    const seoForm = document.getElementById("seoForm");
    if (!seoForm) return;

    seoForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const formData = new FormData(this);
        const submitBtn = this.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...';
        submitBtn.disabled = true;

        fetch("/admin/seo/save/", {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "X-Requested-With": "XMLHttpRequest",
            },
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then((data) => {
                if (data.success) {
                    showAlert("SEO sozlamalari saqlandi!", "success");
                    loadSEOStatus();
                } else {
                    showAlert("Xatolik: " + (data.error || "Noma'lum xatolik"), "error");
                }
            })
            .catch((error) => {
                console.error("SEO save error:", error);
                showAlert("Xatolik yuz berdi: " + error.message, "error");
            })
            .finally(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            });
    });

    // Setup sitemap update button
    const updateSitemapBtn = document.getElementById("update-sitemap-btn");
    if (updateSitemapBtn) {
        updateSitemapBtn.addEventListener("click", updateSitemap);
    }

    // Setup robots.txt update button
    const updateRobotsBtn = document.getElementById("update-robots-btn");
    if (updateRobotsBtn) {
        updateRobotsBtn.addEventListener("click", updateRobots);
    }
}

function loadSEO() {
    const form = document.getElementById("seoForm");
    if (!form) return;

    fetch("/admin/seo/", {
        headers: {
            "X-Requested-With": "XMLHttpRequest",
        },
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then((data) => {
            if (data.success && data.seo) {
                // Populate form fields safely
                const fields = {
                    site_title: data.seo.meta_title || "",
                    site_description: data.seo.meta_description || "",
                    site_keywords: data.seo.meta_keywords || "",
                    publisher_name: data.seo.publisher_name || "",
                };
                // Set text inputs
                Object.keys(fields).forEach((fieldName) => {
                    const field = form.querySelector(`[name="${fieldName}"]`);
                    if (field) {
                        field.value = fields[fieldName];
                    }
                });
                // Set checkboxes
                const scholarCheckbox = form.querySelector('[name="enable_google_scholar"]');
                if (scholarCheckbox) {
                    scholarCheckbox.checked = !!data.seo.enable_google_scholar;
                }
                const sitemapCheckbox = form.querySelector('[name="auto_sitemap"]');
                if (sitemapCheckbox) {
                    sitemapCheckbox.checked = data.seo.auto_sitemap !== false;
                }
                // Load SEO status after loading settings
                loadSEOStatus();
            } else {
                showAlert("SEO ma'lumotlarini yuklashda xatolik: " + (data.error || "Ma'lumot topilmadi"), "error");
                // Initialize with default values
                const sitemapCheckbox = form.querySelector('[name="auto_sitemap"]');
                if (sitemapCheckbox) {
                    sitemapCheckbox.checked = true;
                }
            }
        })
        .catch((error) => {
            console.error("SEO load error:", error);
            showAlert("Xatolik yuz berdi: " + error.message, "error");
            // Initialize with default values on error
            const sitemapCheckbox = form.querySelector('[name="auto_sitemap"]');
            if (sitemapCheckbox) {
                sitemapCheckbox.checked = true;
            }
        });
}

function loadSEOStatus() {
    const statusContainer = document.getElementById("seo-status-container");
    const statsContainer = document.getElementById("seo-stats-container");
    if (!statusContainer) return;

    fetch("/admin/seo/status/", {
        headers: {
            "X-Requested-With": "XMLHttpRequest",
        },
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then((data) => {
            if (data.success) {
                // Update status display
                statusContainer.innerHTML = `
          <div class="small">
            <div class="d-flex justify-content-between mb-2">
              <span>Google Scholar:</span>
              <span class="badge ${data.seo_enabled ? "bg-success" : "bg-secondary"}">
                ${data.seo_enabled ? "Yoqilgan" : "O'chirilgan"}
              </span>
            </div>
            <div class="d-flex justify-content-between mb-2">
              <span>Avtomatik Sitemap:</span>
              <span class="badge ${data.auto_sitemap ? "bg-success" : "bg-warning"}">
                ${data.auto_sitemap ? "Faol" : "Nofaol"}
              </span>
            </div>
          </div>
        `;
                // Update statistics
                if (statsContainer && data.stats) {
                    statsContainer.innerHTML = `
            <div class="small">
              <div class="d-flex justify-content-between mb-1">
                <span>Maqolalar:</span>
                <span class="badge bg-info">${data.stats.articles || 0}</span>
              </div>
              <div class="d-flex justify-content-between mb-1">
                <span>Jurnallar:</span>
                <span class="badge bg-info">${data.stats.journals || 0}</span>
              </div>
              <div class="d-flex justify-content-between mb-1">
                <span>Mualliflar:</span>
                <span class="badge bg-info">${data.stats.authors || 0}</span>
              </div>
              <div class="d-flex justify-content-between mb-1">
                <span>Sonlar:</span>
                <span class="badge bg-info">${data.stats.issues || 0}</span>
              </div>
            </div>
          `;
                }
            } else {
                statusContainer.innerHTML = '<small class="text-danger">Holat ma\'lumotlarini yuklashda xatolik</small>';
                if (statsContainer) {
                    statsContainer.innerHTML = '<small class="text-danger">Statistika mavjud emas</small>';
                }
            }
        })
        .catch((error) => {
            console.error("SEO status error:", error);
            statusContainer.innerHTML = '<small class="text-danger">Xatolik yuz berdi</small>';
            if (statsContainer) {
                statsContainer.innerHTML = '<small class="text-danger">Statistika yuklanmadi</small>';
            }
        });
}

function updateSitemap() {
    const btn = document.getElementById("update-sitemap-btn");
    if (!btn) return;

    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Yangilanmoqda...';
    btn.disabled = true;

    fetch("/admin/seo/update-sitemap/", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken(),
            "X-Requested-With": "XMLHttpRequest",
        },
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then((data) => {
            if (data.success) {
                showAlert(data.message, "success");
                // Show additional stats if available
                if (data.stats) {
                    const statsMsg = `Sitemap yangilandi: ${data.stats.articles} maqola, ${data.stats.journals} jurnal, ${data.stats.authors} muallif`;
                    setTimeout(() => showAlert(statsMsg, "info"), 1000);
                }
                // Refresh status
                loadSEOStatus();
            } else {
                showAlert("Sitemap yangilashda xatolik: " + (data.error || "Noma'lum xatolik"), "error");
            }
        })
        .catch((error) => {
            console.error("Sitemap update error:", error);
            showAlert("Xatolik yuz berdi: " + error.message, "error");
        })
        .finally(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
}

function updateRobots() {
    const btn = document.getElementById("update-robots-btn");
    if (!btn) return;

    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Yangilanmoqda...';
    btn.disabled = true;

    fetch("/admin/seo/update-robots/", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCSRFToken(),
            "X-Requested-With": "XMLHttpRequest",
        },
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then((data) => {
            if (data.success) {
                showAlert(data.message, "success");
                // Show content preview if available
                if (data.content_preview) {
                    setTimeout(() => {
                        showAlert("Robots.txt preview: " + data.content_preview, "info");
                    }, 1000);
                }
                // Refresh status
                loadSEOStatus();
            } else {
                showAlert("Robots.txt yangilashda xatolik: " + (data.error || "Noma'lum xatolik"), "error");
            }
        })
        .catch((error) => {
            console.error("Robots.txt update error:", error);
            showAlert("Xatolik yuz berdi: " + error.message, "error");
        })
        .finally(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
        });
}

// ## UTILITIES SECTION (Fan Tarmoq & Ilmiy Nashr) ##
function setupFanTarmoqForm() {
    const addFanTarmoqForm = document.getElementById("addFanTarmoqForm");
    const editFanTarmoqForm = document.getElementById("editFanTarmoqForm");

    if (addFanTarmoqForm) {
        addFanTarmoqForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...';
            submitBtn.disabled = true;

            fetch("/admin/fan-tarmoq/add/", {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "X-Requested-With": "XMLHttpRequest",
                },
            })
                .then((response) => {
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    return response.json();
                })
                .then((data) => {
                    if (data.success) {
                        showAlert("Fan tarmoq muvaffaqiyatli qo'shildi!", "success");
                        this.reset();
                        const modal = bootstrap.Modal.getInstance(document.getElementById("addFanTarmoqModal"));
                        if (modal) modal.hide();
                        loadFanTarmoqs();
                    } else {
                        showAlert("Xatolik: " + (data.error || "Noma'lum xatolik"), "error");
                    }
                })
                .catch((error) => {
                    console.error("Fan Tarmoq qo'shishda xatolik:", error);
                    showAlert("Xatolik yuz berdi: " + error.message, "error");
                })
                .finally(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                });
        });
    }

    if (editFanTarmoqForm) {
        editFanTarmoqForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const formData = new FormData(this);
            const fanTarmoqId = formData.get("fan_tarmoq_id");
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...';
            submitBtn.disabled = true;

            fetch(`/admin/fan-tarmoq/update/${fanTarmoqId}/`, {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "X-Requested-With": "XMLHttpRequest",
                },
            })
                .then((response) => {
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    return response.json();
                })
                .then((data) => {
                    if (data.success) {
                        showAlert("Fan tarmoq muvaffaqiyatli yangilandi!", "success");
                        const modal = bootstrap.Modal.getInstance(document.getElementById("editFanTarmoqModal"));
                        if (modal) modal.hide();
                        loadFanTarmoqs();
                    } else {
                        showAlert("Xatolik: " + (data.error || "Noma'lum xatolik"), "error");
                    }
                })
                .catch((error) => {
                    console.error("Fan Tarmoq yangilashda xatolik:", error);
                    showAlert("Xatolik yuz berdi: " + error.message, "error");
                })
                .finally(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                });
        });
    }
}

function loadFanTarmoqs() {
    const loadingDiv = document.getElementById("fan-tarmoq-loading");
    if (loadingDiv) loadingDiv.style.display = "block";

    fetch("/admin/fan-tarmoq/list/")
        .then((response) => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then((data) => {
            if (data.success) {
                updateFanTarmoqTable(data.fan_tarmoqs || []);
            } else {
                showAlert("Fan tarmoqlarini yuklashda xatolik: " + (data.error || "Noma'lum xatolik"), "error");
            }
        })
        .catch((error) => {
            console.error("Fan Tarmoq load error:", error);
            showAlert("Xatolik yuz berdi: " + error.message, "error");
        })
        .finally(() => {
            if (loadingDiv) loadingDiv.style.display = "none";
        });
}

function updateFanTarmoqTable(fanTarmoqs) {
    const tbody = document.getElementById("fan-tarmoq-table-body");
    if (!tbody) return;

    tbody.innerHTML = "";

    if (!fanTarmoqs || fanTarmoqs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center">Fan tarmoqlari mavjud emas</td></tr>';
        return;
    }

    fanTarmoqs.forEach((ft) => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${escapeHtml(ft.name)}</td>
            <td>${escapeHtml(ft.description || "-")}</td>
            <td>
                ${ft.is_active ? '<span class="badge bg-success">Faol</span>' : '<span class="badge bg-secondary">Nofaol</span>'}
            </td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-sm btn-primary edit-fan-tarmoq" data-id="${ft.id}" title="Tahrirlash">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger delete-fan-tarmoq" data-id="${ft.id}" title="O'chirish">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });

    // Attach event listeners for edit and delete
    document.querySelectorAll(".edit-fan-tarmoq").forEach((btn) => {
        btn.addEventListener("click", () => editFanTarmoq(btn.dataset.id));
    });

    document.querySelectorAll(".delete-fan-tarmoq").forEach((btn) => {
        btn.addEventListener("click", () => deleteFanTarmoq(btn.dataset.id));
    });
}

function editFanTarmoq(fanTarmoqId) {
    fetch(`/admin/fan-tarmoq/${fanTarmoqId}/edit/`)
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                const ft = data.fan_tarmoq;
                const form = document.getElementById("editFanTarmoqForm");
                form.querySelector('[name="fan_tarmoq_id"]').value = ft.id;
                form.querySelector('[name="name"]').value = ft.name || "";
                form.querySelector('[name="description"]').value = ft.description || "";
                form.querySelector('[name="is_active"]').checked = ft.is_active;

                const modal = new bootstrap.Modal(document.getElementById("editFanTarmoqModal"));
                modal.show();
            } else {
                showAlert("Fan tarmoq ma'lumotlarini olishda xatolik: " + (data.error || "Noma'lum xatolik"), "error");
            }
        })
        .catch((error) => showAlert("Xatolik: " + error.message, "error"));
}

function deleteFanTarmoq(fanTarmoqId) {
    showDeleteConfirmation(
        "Fan Tarmoq",
        `/admin/fan-tarmoq/${fanTarmoqId}/delete/`,
        loadFanTarmoqs
    );
}

// ## Ilmiy Nashr Functions ##
function setupIlmiyNashrForm() {
    const addIlmiyNashrForm = document.getElementById("addIlmiyNashrForm");
    const editIlmiyNashrForm = document.getElementById("editIlmiyNashrForm");

    if (addIlmiyNashrForm) {
        addIlmiyNashrForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...';
            submitBtn.disabled = true;

            fetch("/admin/ilmiy-nashr/add/", {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "X-Requested-With": "XMLHttpRequest",
                },
            })
                .then((response) => {
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    return response.json();
                })
                .then((data) => {
                    if (data.success) {
                        showAlert("Ilmiy nashr turi muvaffaqiyatli qo'shildi!", "success");
                        this.reset();
                        const modal = bootstrap.Modal.getInstance(document.getElementById("addIlmiyNashrModal"));
                        if (modal) modal.hide();
                        loadIlmiyNashrs();
                    } else {
                        showAlert("Xatolik: " + (data.error || "Noma'lum xatolik"), "error");
                    }
                })
                .catch((error) => {
                    console.error("Ilmiy Nashr qo'shishda xatolik:", error);
                    showAlert("Xatolik yuz berdi: " + error.message, "error");
                })
                .finally(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                });
        });
    }

    if (editIlmiyNashrForm) {
        editIlmiyNashrForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const formData = new FormData(this);
            const ilmiyNashrId = formData.get("ilmiy_nashr_id");
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...';
            submitBtn.disabled = true;

            fetch(`/admin/ilmiy-nashr/${ilmiyNashrId}/edit/`, {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "X-Requested-With": "XMLHttpRequest",
                },
            })
                .then((response) => {
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    return response.json();
                })
                .then((data) => {
                    if (data.success) {
                        showAlert("Ilmiy nashr turi muvaffaqiyatli yangilandi!", "success");
                        const modal = bootstrap.Modal.getInstance(document.getElementById("editIlmiyNashrModal"));
                        if (modal) modal.hide();
                        loadIlmiyNashrs();
                    } else {
                        showAlert("Xatolik: " + (data.error || "Noma'lum xatolik"), "error");
                    }
                })
                .catch((error) => {
                    console.error("Ilmiy Nashr yangilashda xatolik:", error);
                    showAlert("Xatolik yuz berdi: " + error.message, "error");
                })
                .finally(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                });
        });
    }
}

function loadIlmiyNashrs() {
    const loadingDiv = document.getElementById("ilmiy-nashr-loading");
    if (loadingDiv) loadingDiv.style.display = "block";

    fetch("/admin/ilmiy-nashr/list/")
        .then((response) => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then((data) => {
            if (data.success) {
                updateIlmiyNashrTable(data.ilmiy_nashrs || []);
            } else {
                showAlert("Ilmiy nashr turlarini yuklashda xatolik: " + (data.error || "Noma'lum xatolik"), "error");
            }
        })
        .catch((error) => {
            console.error("Ilmiy Nashr load error:", error);
            showAlert("Xatolik yuz berdi: " + error.message, "error");
        })
        .finally(() => {
            if (loadingDiv) loadingDiv.style.display = "none";
        });
}

function updateIlmiyNashrTable(ilmiyNashrs) {
    const tbody = document.getElementById("ilmiy-nashr-table-body");
    if (!tbody) return;

    tbody.innerHTML = "";

    if (!ilmiyNashrs || ilmiyNashrs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center">Ilmiy nashr turlari mavjud emas</td></tr>';
        return;
    }

    ilmiyNashrs.forEach((inItem) => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${escapeHtml(inItem.name)}</td>
            <td>${escapeHtml(inItem.description || "-")}</td>
            <td>
                ${inItem.is_active ? '<span class="badge bg-success">Faol</span>' : '<span class="badge bg-secondary">Nofaol</span>'}
            </td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-sm btn-primary edit-ilmiy-nashr" data-id="${inItem.id}" title="Tahrirlash">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger delete-ilmiy-nashr" data-id="${inItem.id}" title="O'chirish">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });

    // Attach event listeners for edit and delete
    document.querySelectorAll(".edit-ilmiy-nashr").forEach((btn) => {
        btn.addEventListener("click", () => editIlmiyNashr(btn.dataset.id));
    });

    document.querySelectorAll(".delete-ilmiy-nashr").forEach((btn) => {
        btn.addEventListener("click", () => deleteIlmiyNashr(btn.dataset.id));
    });
}

function editIlmiyNashr(ilmiyNashrId) {
    fetch(`/admin/ilmiy-nashr/${ilmiyNashrId}/edit/`)
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                const inItem = data.ilmiy_nashr;
                const form = document.getElementById("editIlmiyNashrForm");
                form.querySelector('[name="ilmiy_nashr_id"]').value = inItem.id;
                form.querySelector('[name="name"]').value = inItem.name || "";
                form.querySelector('[name="description"]').value = inItem.description || "";
                form.querySelector('[name="is_active"]').checked = inItem.is_active;

                const modal = new bootstrap.Modal(document.getElementById("editIlmiyNashrModal"));
                modal.show();
            } else {
                showAlert("Ilmiy nashr ma'lumotlarini olishda xatolik: " + (data.error || "Noma'lum xatolik"), "error");
            }
        })
        .catch((error) => showAlert("Xatolik: " + error.message, "error"));
}

function deleteIlmiyNashr(ilmiyNashrId) {
    showDeleteConfirmation(
        "Ilmiy Nashr",
        `/admin/ilmiy-nashr/${ilmiyNashrId}/delete/`,
        loadIlmiyNashrs
    );
}

// ## NEW: NAVIGATION FOR PUBLISHERS SECTION ##
function loadNavigations() {
    const loadingDiv = document.getElementById("navigation-loading");
    if (loadingDiv) loadingDiv.style.display = "block";

    fetch("/admin/navigation/list/")
        .then((response) => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.json();
        })
        .then((data) => {
            if (data.success) {
                updateNavigationTable(data.navigations || []);
            } else {
                showAlert("Navigatsiyalarni yuklashda xatolik: " + (data.error || "Noma'lum xatolik"), "error");
            }
        })
        .catch((error) => {
            console.error("Navigation load error:", error);
            showAlert("Xatolik yuz berdi: " + error.message, "error");
        })
        .finally(() => {
            if (loadingDiv) loadingDiv.style.display = "none";
        });
}

function updateNavigationTable(navigations) {
    const tbody = document.getElementById("navigation-table-body");
    if (!tbody) return;

    tbody.innerHTML = "";

    if (!navigations || navigations.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center">Navigatsiyalar mavjud emas</td></tr>';
        return;
    }

    navigations.forEach((nav) => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${escapeHtml(nav.name)}</td>
            <td><span class="badge bg-info">${nav.item_count}</span></td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-sm btn-primary edit-navigation" data-id="${nav.id}" title="Tahrirlash">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-danger delete-navigation" data-id="${nav.id}" title="O'chirish">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });

    // Attach event listeners for edit and delete
    document.querySelectorAll(".edit-navigation").forEach((btn) => {
        btn.addEventListener("click", () => editNavigation(btn.dataset.id));
    });

    document.querySelectorAll(".delete-navigation").forEach((btn) => {
        btn.addEventListener("click", () => deleteNavigation(btn.dataset.id));
    });
}

function setupNavigationForm() {
    const addNavigationForm = document.getElementById("addNavigationForm");
    const editNavigationForm = document.getElementById("editNavigationForm");

    if (addNavigationForm) {
        addNavigationForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...';
            submitBtn.disabled = true;

            fetch("/admin/navigation/add/", {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "X-Requested-With": "XMLHttpRequest",
                },
            })
                .then((response) => {
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    return response.json();
                })
                .then((data) => {
                    if (data.success) {
                        showAlert("Navigatsiya muvaffaqiyatli qo'shildi!", "success");
                        this.reset();
                        const modal = bootstrap.Modal.getInstance(document.getElementById("addNavigationModal"));
                        if (modal) modal.hide();
                        loadNavigations();
                    } else {
                        showAlert("Xatolik: " + (data.error || "Noma'lum xatolik"), "error");
                    }
                })
                .catch((error) => {
                    console.error("Navigation qo'shishda xatolik:", error);
                    showAlert("Xatolik yuz berdi: " + error.message, "error");
                })
                .finally(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                });
        });
    }

    if (editNavigationForm) {
        editNavigationForm.addEventListener("submit", function (e) {
            e.preventDefault();
            const formData = new FormData(this);
            const navigationId = formData.get("navigation_id");
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saqlanmoqda...';
            submitBtn.disabled = true;

            fetch(`/admin/navigation/update/${navigationId}/`, {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "X-Requested-With": "XMLHttpRequest",
                },
            })
                .then((response) => {
                    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                    return response.json();
                })
                .then((data) => {
                    if (data.success) {
                        showAlert("Navigatsiya muvaffaqiyatli yangilandi!", "success");
                        const modal = bootstrap.Modal.getInstance(document.getElementById("editNavigationModal"));
                        if (modal) modal.hide();
                        loadNavigations();
                    } else {
                        showAlert("Xatolik: " + (data.error || "Noma'lum xatolik"), "error");
                    }
                })
                .catch((error) => {
                    console.error("Navigation yangilashda xatolik:", error);
                    showAlert("Xatolik yuz berdi: " + error.message, "error");
                })
                .finally(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                });
        });
    }
}

function editNavigation(navigationId) {
    fetch(`/admin/navigation/update/${navigationId}/`)
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                const nav = data.navigation;
                const form = document.getElementById("editNavigationForm");
                form.querySelector('[name="navigation_id"]').value = nav.id;
                form.querySelector('[name="name"]').value = nav.name;

                // Clear existing items
                const itemsContainer = document.getElementById("edit-navigation-items-container");
                if (itemsContainer) {
                    itemsContainer.innerHTML = "";
                    nav.items.forEach((item, index) => {
                        addItemInput(itemsContainer, item.text, item.id);
                    });
                }

                const modal = new bootstrap.Modal(document.getElementById("editNavigationModal"));
                modal.show();
            } else {
                showAlert("Navigatsiya ma'lumotlarini olishda xatolik: " + (data.error || "Noma'lum xatolik"), "error");
            }
        })
        .catch((error) => showAlert("Xatolik: " + error.message, "error"));
}

function deleteNavigation(navigationId) {
    showDeleteConfirmation(
        "Navigatsiya",
        `/admin/navigation/delete/${navigationId}/`,
        loadNavigations
    );
}

function addItemInput(container, text = "", itemId = null) {
    const itemDiv = document.createElement("div");
    itemDiv.className = "navigation-item-row mb-2";
    itemDiv.innerHTML = `
        <div class="input-group">
            <input type="text" class="form-control" name="items[]" value="${escapeHtml(text)}" placeholder="Navigatsiya elementi matni" required>
            <button class="btn btn-outline-danger remove-item" type="button">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
    container.appendChild(itemDiv);

    itemDiv.querySelector(".remove-item").addEventListener("click", function () {
        container.removeChild(itemDiv);
    });
}

// Initialize Navigation form handlers
function initializeNavigationForms() {
    const addItemsBtn = document.getElementById("add-navigation-item");
    const editItemsBtn = document.getElementById("add-edit-navigation-item");

    if (addItemsBtn) {
        addItemsBtn.addEventListener("click", function () {
            const container = document.getElementById("add-navigation-items-container");
            if (container) {
                addItemInput(container);
            }
        });
    }

    if (editItemsBtn) {
        editItemsBtn.addEventListener("click", function () {
            const container = document.getElementById("edit-navigation-items-container");
            if (container) {
                addItemInput(container);
            }
        });
    }
}

// ## GLOBAL EXPORT FUNCTION ##
function exportArticles() {
    window.location.href = "/admin/export/articles/";
}

// ## UTILITY SECTION (General Functions) ##
function setupFormHandlers() {
    setupJournalForm();
    setupSEOForm();
    setupAuthorFormHandlers();
    setupFanTarmoqForm();
    setupIlmiyNashrForm();
    setupNavigationForm(); // NEW: Setup Navigation Form
    initializeNavigationForms(); // NEW: Initialize Navigation Item handlers
}

function updatePagination(type, pagination) {
    const paginationEl = document.getElementById(`${type}-pagination`);
    if (!paginationEl || !pagination) return;
    let html = "";
    if (pagination.has_previous) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="load${capitalize(type)}(${pagination.current - 1}); return false;"><i class="fas fa-chevron-left"></i></a></li>`;
    }
    for (let i = 1; i <= pagination.total_pages; i++) {
        if (i === pagination.current) {
            html += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
        } else if (
            i === 1 ||
            i === pagination.total_pages ||
            (i >= pagination.current - 2 && i <= pagination.current + 2)
        ) {
            html += `<li class="page-item"><a class="page-link" href="#" onclick="load${capitalize(type)}(${i}); return false;">${i}</a></li>`;
        } else if (i === pagination.current - 3 || i === pagination.current + 3) {
            html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
        }
    }
    if (pagination.has_next) {
        html += `<li class="page-item"><a class="page-link" href="#" onclick="load${capitalize(type)}(${pagination.current + 1}); return false;"><i class="fas fa-chevron-right"></i></a></li>`;
    }
    paginationEl.innerHTML = html;
}

function showDeleteConfirmation(entityName, deleteUrl, callback) {
    document.getElementById("deleteConfirmMessage").textContent = `${entityName}ni o\'chirishni xohlaysizmi? Bu amalni ortga qaytarib bo\'lmaydi.`;
    deleteCallback = () => {
        fetch(deleteUrl, {
            method: "POST",
            headers: {"X-CSRFToken": getCSRFToken()},
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    showAlert(`${entityName} o\'chirildi!`, "success");
                    if (typeof callback === "function") {
                        callback();
                    }
                } else {
                    showAlert("Xatolik: " + (data.error || "O'chirib bo'lmadi"), "error");
                }
            })
            .catch((error) => showAlert("Xatolik: " + error.message, "error"));
    };
    const modal = new bootstrap.Modal(document.getElementById("deleteConfirmModal"));
    modal.show();
}

function showAlert(message, type = "info") {
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert alert-${type === "error" ? "danger" : type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = "top: 20px; right: 20px; z-index: 9999; min-width: 300px;";
    const iconMap = {
        success: "check-circle",
        error: "exclamation-triangle",
        warning: "exclamation-triangle",
        info: "info-circle",
    };
    alertDiv.innerHTML = `
        <i class="fas fa-${iconMap[type] || "info-circle"} me-2"></i>
        ${escapeHtml(message)}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    setTimeout(() => {
        const alert = bootstrap.Alert.getOrCreateInstance(alertDiv);
        if (alert) alert.close();
    }, 5000);
}

function getCSRFToken() {
    const name = "csrftoken";
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.substring(0, name.length + 1) === name + "=") {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function escapeHtml(text) {
    if (!text) return "";
    const map = {"&": "&amp;", "<": "<", ">": ">", '"': "&quot;", "'": "&#039;"};
    return text.toString().replace(/[&<>"']/g, (m) => map[m]);
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function setupFilters() {
    const statusFilter = document.getElementById("author-filter-status");
    if (statusFilter) {
        statusFilter.addEventListener("change", () => {
            const search = document.getElementById("author-search") ? document.getElementById("author-search").value : "";
            loadAuthors(1, search);
        });
    }
}

function loadInitialData() {
    loadJournals();
    updateJournalSelects();
}

function setupMobileMenu() {
    const toggleBtn = document.querySelector(".mobile-menu-btn");
    const sidebar = document.querySelector(".sidebar");
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener("click", () => sidebar.classList.toggle("show"));
    }
}

function setupModals() {
    const modals = document.querySelectorAll(".modal");
    modals.forEach((modal) => {
        modal.addEventListener("hidden.bs.modal", function () {
            const form = this.querySelector("form");
            if (form) form.reset();
            // Reset Quill editors
            const editorContainers = this.querySelectorAll('[id$="-editor"]');
            editorContainers.forEach((container) => {
                const editorId = "#" + container.id;
                setQuillContent(editorId, "");
            });
        });
    });

    const confirmDeleteBtn = document.getElementById("confirmDeleteBtn");
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener("click", () => {
            if (deleteCallback) {
                deleteCallback();
                deleteCallback = null;
                const modal = bootstrap.Modal.getInstance(document.getElementById("deleteConfirmModal"));
                modal.hide();
            }
        });
    }
}

// Utility: Debounce function for search input
function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}


// Call this after DOM is loaded to initialize navigation forms
document.addEventListener("DOMContentLoaded", function () {
    initializeNavigationForms();
});