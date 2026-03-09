from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.auth.dependencies import (
    require_admin_access,
    require_active_review_requests_read,
    require_admin_templates_read,
)

router = APIRouter(tags=["dev-pages"])


@router.get("/dev/admin", response_class=HTMLResponse)
async def admin_landing_page() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Admin Landing</title>
  <style>
    body { font-family: "Segoe UI", sans-serif; margin: 24px; max-width: 900px; }
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 14px; margin-bottom: 12px; }
    a { text-decoration: none; color: #0b57d0; }
  </style>
</head>
<body>
  <h1>Admin Landing (Dev)</h1>
  <div id="welcomeLine" style="margin: 6px 0 18px; font-weight: 600;"></div>
  <div class="card" id="authCard">
    <h3>Authentication</h3>
    <div id="authState">Loading...</div>
    <div id="authHint" style="margin-top:8px; color:#555;"></div>
    <div style="margin-top:8px;">
      <a href="/auth/login">Login</a>
      <button type="button" onclick="logout()">Logout</button>
      <button type="button" onclick="bootstrapAdmin()">Bootstrap Admin</button>
    </div>
  </div>
  <div class="card" id="pendingCard" style="display:none;">
    <h3>Welcome</h3>
    <div>You are signed in, but do not currently have access to this application.</div>
    <div style="margin-top:6px;">Please contact an administrator to request access.</div>
    <div style="margin-top:10px;">
      <button type="button" onclick="logout()">Logout</button>
      <a href="/auth/login" style="margin-left:8px;">Login with Different Account</a>
    </div>
  </div>
  <div class="card protected-card admin-only" style="display:none;">
    <h3>User Access</h3>
    <div><a href="/dev/user-access-admin">Open User Access Admin</a></div>
    <div style="margin-top:6px;">View users and update role assignments.</div>
  </div>
  <div class="card protected-card admin-only" style="display:none;">
    <h3>Form Templates</h3>
    <div><a href="/dev/admin-form-templates">Open Form Template Manager</a></div>
    <div style="margin-top:6px;">Create/import/export template JSON, view versions, and save new versions.</div>
  </div>
  <div class="card protected-card active-requests-card" style="display:none;">
    <h3>Active Review Requests</h3>
    <div><a href="/dev/active-forms-admin">Open Active Forms Admin</a></div>
    <div style="margin-top:6px;">View in-flight requests and reassign template/version.</div>
  </div>
  <div class="card protected-card admin-only" style="display:none;">
    <h3>Reviewer Test Form</h3>
    <div><a href="/dev/review-form">Open Reviewer Form Test Page</a></div>
    <div style="margin-top:6px;">Preview reviewer rendering and validate/submit payloads.</div>
  </div>
  <script>
    const authState = document.getElementById("authState");
    const authHint = document.getElementById("authHint");
    const authCard = document.getElementById("authCard");
    const pendingCard = document.getElementById("pendingCard");
    function isInternalEmail(email) {
      return /@(greshamsmith\.com|gspnet\.com)$/i.test(email || "");
    }
    function extractFirstName(displayName, email) {
      const rawName = (displayName || "").trim();
      if (rawName) {
        const namePart = rawName.includes(",")
          ? rawName.split(",")[1]?.trim()
          : rawName;
        const token = (namePart || "").split(/\s+/)[0];
        if (token) {
          return token.charAt(0).toUpperCase() + token.slice(1).toLowerCase();
        }
      }
      const local = (email || "").split("@")[0];
      if (!local) return "";
      const firstPart = local.split(".")[0];
      if (!firstPart) return "";
      const cleaned = firstPart.replace(/[_-]+/g, " ").trim();
      if (!cleaned) return "";
      const token = cleaned.split(" ")[0];
      if (!token) return "";
      return token.charAt(0).toUpperCase() + token.slice(1).toLowerCase();
    }
    function setWelcome(body) {
      const welcome = document.getElementById("welcomeLine");
      if (!welcome) return;
      if (!body || body.auth_status !== "authenticated") {
        welcome.textContent = "";
        return;
      }
      const email = body.email || "";
      if (isInternalEmail(email)) {
        const first = extractFirstName(body.display_name, email);
        welcome.textContent = first ? `Welcome, ${first}` : "Welcome";
        return;
      }
      welcome.textContent = "Welcome";
    }
    async function refreshAuth() {
      const response = await fetch("/me");
      const body = await response.json();
      if (!response.ok) {
        authState.textContent = "Failed to load auth state";
        return;
      }
      authState.textContent = JSON.stringify(body, null, 2);
      setWelcome(body);
      const cards = [...document.querySelectorAll(".protected-card")];
      const adminOnly = [...document.querySelectorAll(".admin-only")];
      const activeRequestsCard = document.querySelector(".active-requests-card");
      const isAuthenticated = body && body.auth_status === "authenticated";
      const isActive = body && body.effective_access_state === "active";
      const perms = (body && Array.isArray(body.permissions)) ? body.permissions : [];
      const isAdmin = perms.includes("admin.access");
      const canViewActiveRequests = isAdmin || (
        perms.includes("internal.form.read") && perms.includes("internal.assignment.read")
      );
      if (!isAuthenticated) {
        authHint.textContent = "Sign in to access admin/reviewer tools.";
        authCard.style.display = "block";
        pendingCard.style.display = "none";
      } else if (!isActive) {
        authHint.textContent = "";
        authCard.style.display = "none";
        pendingCard.style.display = "block";
      } else {
        authHint.textContent = "Access is active.";
        authCard.style.display = "block";
        pendingCard.style.display = "none";
      }
      cards.forEach(card => { card.style.display = "none"; });
      if (isActive) {
        adminOnly.forEach(card => { card.style.display = isAdmin ? "block" : "none"; });
        if (activeRequestsCard) {
          activeRequestsCard.style.display = canViewActiveRequests ? "block" : "none";
        }
      }
    }
    async function logout() {
      await fetch("/auth/logout", { method: "POST" });
      await refreshAuth();
    }
    async function bootstrapAdmin() {
      const response = await fetch("/auth/bootstrap-admin", { method: "POST" });
      const body = await response.json();
      alert(JSON.stringify(body, null, 2));
      await refreshAuth();
    }
    refreshAuth();
  </script>
</body>
</html>
"""


@router.get(
    "/dev/user-access-admin",
    response_class=HTMLResponse,
    dependencies=[Depends(require_admin_access)],
)
async def user_access_admin_page() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>User Access Admin</title>
  <style>
    body { font-family: "Segoe UI", sans-serif; margin: 24px; max-width: 1400px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; vertical-align: top; font-size: 0.9rem; }
    th { background: #f5f5f5; text-align: left; }
    input, select, button { margin-right: 6px; margin-bottom: 4px; }
    .toolbar { margin-bottom: 12px; }
    pre { background: #f8f8f8; padding: 12px; white-space: pre-wrap; }
    .result-error { color: #b42318; }
    .banner { border-radius: 6px; padding: 10px 12px; margin: 12px 0; display: none; }
    .banner-error { border: 1px solid #b42318; background: #fef3f2; color: #7a271a; }
  </style>
</head>
<body>
  <div style="margin-bottom:12px;">
    <a href="/dev/admin">Home</a> |
    <a href="/dev/user-access-admin">User Access Admin</a> |
    <a href="/dev/admin-form-templates">Template Manager</a> |
    <a href="/dev/active-forms-admin">Active Forms</a> |
    <a href="/dev/review-form">Reviewer Test Form</a> 
  </div>
  <h1>User Access Admin (Dev)</h1>
  <div id="welcomeLine" style="margin: 6px 0 18px; font-weight: 600;"></div>
  <div class="toolbar">
    <button onclick="loadData()">Refresh</button>
    <a href="/auth/login">Login</a>
    <button type="button" onclick="logout()">Logout</button>
  </div>
  <div id="errorBanner" class="banner banner-error"></div>
  <div id="tableWrap"></div>
  <h3>Result</h3>
  <pre id="result"></pre>
  <script>
    const result = document.getElementById("result");
    const errorBanner = document.getElementById("errorBanner");
    let roleNames = [];
    function show(value) {
      result.className = "";
      result.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
      errorBanner.style.display = "none";
      errorBanner.textContent = "";
    }
    function showError(value) {
      result.className = "result-error";
      result.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
      errorBanner.textContent =
        typeof value === "string" ? value : JSON.stringify(value, null, 2);
      errorBanner.style.display = "block";
    }
    async function apiFetch(url, options = null) {
      const response = await fetch(url, options || undefined);
      const body = await response.json();
      return { response, body };
    }
    function isInternalEmail(email) {
      return /@(greshamsmith\.com|gspnet\.com)$/i.test(email || "");
    }
    function extractFirstName(displayName, email) {
      const rawName = (displayName || "").trim();
      if (rawName) {
        const namePart = rawName.includes(",")
          ? rawName.split(",")[1]?.trim()
          : rawName;
        const token = (namePart || "").split(/\s+/)[0];
        if (token) {
          return token.charAt(0).toUpperCase() + token.slice(1).toLowerCase();
        }
      }
      const local = (email || "").split("@")[0];
      if (!local) return "";
      const firstPart = local.split(".")[0];
      if (!firstPart) return "";
      const cleaned = firstPart.replace(/[_-]+/g, " ").trim();
      if (!cleaned) return "";
      const token = cleaned.split(" ")[0];
      if (!token) return "";
      return token.charAt(0).toUpperCase() + token.slice(1).toLowerCase();
    }
    function setWelcome(body) {
      const welcome = document.getElementById("welcomeLine");
      if (!welcome) return;
      if (!body || body.auth_status !== "authenticated") {
        welcome.textContent = "";
        return;
      }
      const email = body.email || "";
      if (isInternalEmail(email)) {
        const first = extractFirstName(body.display_name, email);
        welcome.textContent = first ? `Welcome, ${first}` : "Welcome";
        return;
      }
      welcome.textContent = "Welcome";
    }
    async function loadAuthAndWelcome() {
      const { response, body } = await apiFetch("/me");
      if (response.ok) {
        setWelcome(body);
      }
    }
    async function logout() {
      await fetch("/auth/logout", { method: "POST" });
      window.location.href = "/dev/admin";
    }
    function renderRoleCheckboxes(currentRoles, appUserId) {
      return roleNames.map(role => {
        const checked = currentRoles.includes(role) ? "checked" : "";
        return `<label style="display:block;"><input type="checkbox" data-role="role-${appUserId}" value="${role}" ${checked}/> ${role}</label>`;
      }).join("");
    }
    async function loadData() {
      const rolesResp = await apiFetch("/admin/user-access/roles");
      if (!rolesResp.response.ok) return showError(rolesResp.body);
      roleNames = (rolesResp.body || []).map(x => x.role_name);

      const usersResp = await apiFetch("/admin/user-access/users");
      if (!usersResp.response.ok) return showError(usersResp.body);
      const users = usersResp.body || [];
      if (!users.length) {
        document.getElementById("tableWrap").innerHTML = "<div>No users found.</div>";
        return show(usersResp.body);
      }
      const rows = users.map(u => `
        <tr data-user-id="${u.app_user_id}">
          <td>${u.display_name || ""}<br>${u.email || ""}</td>
          <td>${u.app_user_id}</td>
          <td>${u.entra_object_id}</td>
          <td>${u.roles.join(", ")}</td>
          <td>${u.permissions.join(", ")}</td>
          <td>
            <label><input type="checkbox" data-flag="is_active" ${u.is_active ? "checked" : ""}/> active</label><br>
            <label><input type="checkbox" data-flag="is_approved" ${u.is_approved ? "checked" : ""}/> approved</label>
          </td>
          <td>${renderRoleCheckboxes(u.roles, u.app_user_id)}</td>
          <td><button type="button" onclick="saveUser(this)">Save</button></td>
        </tr>
      `).join("");
      document.getElementById("tableWrap").innerHTML = `
        <table>
          <thead>
            <tr>
              <th>User</th>
              <th>App User ID</th>
              <th>Entra Object ID</th>
              <th>Roles</th>
              <th>Permissions</th>
              <th>Status</th>
              <th>Edit Roles</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      `;
      show(usersResp.body);
    }
    async function saveUser(button) {
      const row = button.closest("tr");
      const appUserId = row.getAttribute("data-user-id");
      const roleChecks = [...row.querySelectorAll(`input[data-role='role-${appUserId}']`)];
      const roles = roleChecks.filter(x => x.checked).map(x => x.value);
      const isActive = !!row.querySelector("input[data-flag='is_active']").checked;
      const isApproved = !!row.querySelector("input[data-flag='is_approved']").checked;
      const { response, body } = await apiFetch(`/admin/user-access/users/${appUserId}/roles`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ roles, is_active: isActive, is_approved: isApproved })
      });
      if (!response.ok) {
        const message = body && body.detail ? body.detail : body;
        showError(message);
        return;
      }
      show(body);
      await loadData();
    }
    (async () => {
      await loadAuthAndWelcome();
      await loadData();
    })();
  </script>
</body>
</html>
"""


@router.get(
    "/dev/admin-form-templates",
    response_class=HTMLResponse,
    dependencies=[Depends(require_admin_templates_read)],
)
async def admin_form_templates_page() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Admin Form Template Editor</title>
  <style>
    body { font-family: "Segoe UI", sans-serif; margin: 24px; max-width: 1100px; }
    textarea { width: 100%; min-height: 380px; font-family: Consolas, monospace; }
    input, button { margin-right: 8px; margin-bottom: 8px; }
    .row { display: flex; gap: 12px; flex-wrap: wrap; }
    .card { border: 1px solid #ddd; padding: 12px; border-radius: 6px; }
    pre { background: #f8f8f8; padding: 12px; white-space: pre-wrap; }
    .banner { border-radius: 6px; padding: 10px 12px; margin: 12px 0; display: none; }
    .banner h3 { margin: 0 0 6px 0; font-size: 1rem; }
    .banner ul { margin: 0; padding-left: 18px; }
    .banner-success { border: 1px solid #0f766e; background: #ecfdf5; color: #115e59; }
    .banner-error { border: 1px solid #b42318; background: #fef3f2; color: #7a271a; }
  </style>
</head>
<body>
  <div style="margin-bottom:12px;">
    <a href="/dev/admin">Home</a> |
    <a href="/dev/user-access-admin">User Access Admin</a> |
    <a href="/dev/admin-form-templates">Template Manager</a> |
    <a href="/dev/active-forms-admin">Active Forms</a> |
    <a href="/dev/review-form">Reviewer Test Form</a> 
  </div>
  <div class="card">
    <strong>Auth State:</strong>
    <pre id="authState" style="margin-top:8px;">Loading...</pre>
    <a href="/auth/login">Login</a>
    <button type="button" onclick="logout()">Logout</button>
  </div>
  <h1>Admin Form Template Editor (Dev)</h1>
  <div id="welcomeLine" style="margin: 6px 0 18px; font-weight: 600;"></div>
  <div id="successBanner" class="banner banner-success"></div>
  <div id="errorBanner" class="banner banner-error"></div>
  <div class="row">
    <div class="card">
      <div><label>Template Key <input id="templateKey" value="qc_subconsultant_review" /></label></div>
      <div>
        <label>Version
          <select id="versionSelect">
            <option value="1">v1</option>
          </select>
        </label>
      </div>
      <button onclick="loadVersion()">Load Version</button>
      <button onclick="listVersions()">List Versions</button>
      <button onclick="saveVersion()">Save New Version</button>
      <button onclick="importTemplate()">Import JSON File</button>
      <button onclick="exportTemplate()">Export JSON File</button>
    </div>
  </div>
  <input id="importFile" type="file" accept="application/json" style="display:none;" />
  <textarea id="jsonArea"></textarea>
  <h3>Result</h3>
  <pre id="result"></pre>
  <script>
    const starter = {
      schema_json: {
        schema_version: "1.0",
        template_key: "qc_subconsultant_review",
        display_name: "QC Subconsultant Review Form",
        branding: { org_name: "Gresham Smith", logo_url: "/static/images/logo.png" },
        auto_fields: ["project_name","project_number","owner_end_user","submittal_name","submittal_date","reviewer_name"],
        discipline_repeat: {
          source: "review_request_discipline",
          label_field: "discipline_name",
          items: [
            {
              section_key: "off_team_qualified_review",
              section_label: "Off-Team Qualified Review",
              choice: { type: "single_select", options: ["complete", "na"], required: true },
              signature: {
                required_when_choice_selected: true,
                type_name_must_match_reviewer: true,
                match_mode: "case_insensitive_exact",
                capture_timestamp: true
              },
              notes: { type: "text", required: false, max_length: 4000 }
            },
            {
              section_key: "constructability_review",
              section_label: "Constructability Review",
              choice: { type: "single_select", options: ["complete", "na"], required: true },
              signature: {
                required_when_choice_selected: true,
                type_name_must_match_reviewer: true,
                match_mode: "case_insensitive_exact",
                capture_timestamp: true
              },
              notes: { type: "text", required: false, max_length: 4000 }
            }
          ]
        }
      }
    };
    const result = document.getElementById("result");
    const area = document.getElementById("jsonArea");
    const versionSelect = document.getElementById("versionSelect");
    const authState = document.getElementById("authState");
    const successBanner = document.getElementById("successBanner");
    const errorBanner = document.getElementById("errorBanner");
    const importFile = document.getElementById("importFile");
    area.value = JSON.stringify(starter, null, 2);
    function show(value) {
      result.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
    }
    function clearBanners() {
      successBanner.style.display = "none";
      successBanner.textContent = "";
      errorBanner.style.display = "none";
      errorBanner.textContent = "";
    }
    function setBanner(target, title, lines) {
      const list = Array.isArray(lines) && lines.length
        ? `<ul>${lines.map(line => `<li>${line}</li>`).join("")}</ul>`
        : "";
      target.innerHTML = `<h3>${title}</h3>${list}`;
      target.style.display = "block";
    }
    function showSuccess(title, lines) {
      setBanner(successBanner, title, lines);
    }
    function showError(title, lines) {
      setBanner(errorBanner, title, lines);
    }
    async function apiFetch(url, options = null) {
      const response = await fetch(url, options || undefined);
      if (response.status === 401) {
        show({ detail: "Unauthenticated. Use /auth/login first." });
      } else if (response.status === 403) {
        const body = await response.json();
        show(body);
        return { response, body };
      }
      const body = await response.json();
      return { response, body };
    }
    function isInternalEmail(email) {
      return /@(greshamsmith\.com|gspnet\.com)$/i.test(email || "");
    }
    function extractFirstName(displayName, email) {
      const rawName = (displayName || "").trim();
      if (rawName) {
        const namePart = rawName.includes(",")
          ? rawName.split(",")[1]?.trim()
          : rawName;
        const token = (namePart || "").split(/\s+/)[0];
        if (token) {
          return token.charAt(0).toUpperCase() + token.slice(1).toLowerCase();
        }
      }
      const local = (email || "").split("@")[0];
      if (!local) return "";
      const firstPart = local.split(".")[0];
      if (!firstPart) return "";
      const cleaned = firstPart.replace(/[_-]+/g, " ").trim();
      if (!cleaned) return "";
      const token = cleaned.split(" ")[0];
      if (!token) return "";
      return token.charAt(0).toUpperCase() + token.slice(1).toLowerCase();
    }
    function setWelcome(body) {
      const welcome = document.getElementById("welcomeLine");
      if (!welcome) return;
      if (!body || body.auth_status !== "authenticated") {
        welcome.textContent = "";
        return;
      }
      const email = body.email || "";
      if (isInternalEmail(email)) {
        const first = extractFirstName(body.display_name, email);
        welcome.textContent = first ? `Welcome, ${first}` : "Welcome";
        return;
      }
      welcome.textContent = "Welcome";
    }
    function parseJson(input) {
      try {
        return { value: JSON.parse(input), error: null };
      } catch (err) {
        return { value: null, error: err };
      }
    }
    function validateTemplatePayload(payload) {
      const errors = [];
      if (!payload || typeof payload !== "object") {
        errors.push("Root JSON must be an object with a schema_json property.");
        return errors;
      }
      const schema = payload.schema_json;
      if (!schema || typeof schema !== "object") {
        errors.push("schema_json must be an object.");
        return errors;
      }
      if (!schema.schema_version || typeof schema.schema_version !== "string") {
        errors.push("schema_json.schema_version must be a string.");
      }
      if (!schema.template_key || typeof schema.template_key !== "string") {
        errors.push("schema_json.template_key must be a non-empty string.");
      }
      if (!schema.display_name || typeof schema.display_name !== "string") {
        errors.push("schema_json.display_name must be a non-empty string.");
      }
      if (!schema.branding || typeof schema.branding !== "object") {
        errors.push("schema_json.branding must be an object with org_name.");
      } else if (!schema.branding.org_name || typeof schema.branding.org_name !== "string") {
        errors.push("schema_json.branding.org_name must be a non-empty string.");
      }
      if (!Array.isArray(schema.auto_fields) || schema.auto_fields.length === 0) {
        errors.push("schema_json.auto_fields must be a non-empty array.");
      } else {
        const unique = new Set(schema.auto_fields);
        if (unique.size !== schema.auto_fields.length) {
          errors.push("schema_json.auto_fields must not contain duplicate values.");
        }
      }
      const repeat = schema.discipline_repeat;
      if (!repeat || typeof repeat !== "object") {
        errors.push("schema_json.discipline_repeat must be an object.");
      } else if (!Array.isArray(repeat.items) || repeat.items.length === 0) {
        errors.push("schema_json.discipline_repeat.items must include at least one section.");
      } else {
        const keys = repeat.items.map(item => item?.section_key).filter(Boolean);
        if (keys.length !== repeat.items.length) {
          errors.push("Each discipline_repeat item must have a section_key.");
        } else if (new Set(keys).size !== keys.length) {
          errors.push("discipline_repeat.items must not contain duplicate section_key values.");
        }
        repeat.items.forEach((item, index) => {
          if (!item.section_label || typeof item.section_label !== "string") {
            errors.push(`discipline_repeat.items[${index}].section_label must be a non-empty string.`);
          }
          if (!item.choice || typeof item.choice !== "object") {
            errors.push(`discipline_repeat.items[${index}].choice must be an object.`);
          } else {
            if (item.choice.type && item.choice.type !== "single_select") {
              errors.push(`discipline_repeat.items[${index}].choice.type must be "single_select".`);
            }
            if (item.choice.options) {
              const options = Array.isArray(item.choice.options) ? item.choice.options : [];
              const optionSet = new Set(options);
              if (optionSet.size !== 2 || !optionSet.has("complete") || !optionSet.has("na")) {
                errors.push(`discipline_repeat.items[${index}].choice.options must contain "complete" and "na".`);
              }
            }
          }
          if (item.signature && item.signature.match_mode && item.signature.match_mode !== "case_insensitive_exact") {
            errors.push(`discipline_repeat.items[${index}].signature.match_mode must be "case_insensitive_exact".`);
          }
          if (item.notes && item.notes.max_length !== undefined) {
            const maxLength = Number(item.notes.max_length);
            if (!Number.isFinite(maxLength) || maxLength <= 0) {
              errors.push(`discipline_repeat.items[${index}].notes.max_length must be a positive number.`);
            }
          }
        });
      }
      return errors;
    }
    async function loadAuthState() {
      const { response, body } = await apiFetch("/me");
      if (!response.ok) return;
      authState.textContent = JSON.stringify(body, null, 2);
      setWelcome(body);
    }
    async function logout() {
      await fetch("/auth/logout", { method: "POST" });
      await loadAuthState();
    }
    async function loadVersion(versionOverride = null) {
      clearBanners();
      const key = document.getElementById("templateKey").value.trim();
      const version = versionOverride ?? versionSelect.value;
      versionSelect.value = String(version);
      const { response, body } = await apiFetch(`/admin/form-templates/${encodeURIComponent(key)}/versions/${version}`);
      if (!response.ok) return show(body);
      area.value = JSON.stringify({ schema_json: body.version.schema_json }, null, 2);
      show(body);
    }
    async function listVersions() {
      clearBanners();
      const key = document.getElementById("templateKey").value.trim();
      const { response, body } = await apiFetch(`/admin/form-templates/${encodeURIComponent(key)}/versions`);
      if (!response.ok) {
        versionSelect.innerHTML = '<option value="1">v1</option>';
        return show(body);
      }
      if (!Array.isArray(body) || body.length === 0) {
        versionSelect.innerHTML = '<option value="">No versions found</option>';
        return;
      }
      body.sort((a, b) => {
        const da = new Date(a.created_at).getTime();
        const db = new Date(b.created_at).getTime();
        if (db !== da) return db - da;
        return Number(b.version) - Number(a.version);
      });
      const selectedVersion = versionSelect.value;
      versionSelect.innerHTML = body.map(v => {
        const activeLabel = v.is_active ? " (active)" : "";
        return `<option value="${v.version}">v${v.version}${activeLabel}</option>`;
      }).join("");
      const found = body.some(v => String(v.version) === String(selectedVersion));
      if (found) {
        versionSelect.value = selectedVersion;
      }
    }
    async function saveVersion() {
      clearBanners();
      const key = document.getElementById("templateKey").value.trim();
      const parsed = parseJson(area.value);
      if (parsed.error) {
        showError("Save failed", ["Editor JSON is invalid.", "Fix the JSON syntax and try again."]);
        return;
      }
      const validationErrors = validateTemplatePayload(parsed.value);
      if (validationErrors.length) {
        showError("Save failed", validationErrors.concat(["Fix the schema issues above before saving."]));
        return;
      }
      await savePayloadAsVersion(parsed.value, key, "Save successful");
    }
    async function savePayloadAsVersion(payload, templateKey, successTitle) {
      const { response, body } = await apiFetch(`/admin/form-templates/${encodeURIComponent(templateKey)}/versions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      show(body);
      if (response.ok && body?.version?.version) {
        await listVersions();
        versionSelect.value = String(body.version.version);
        showSuccess(successTitle, [`Saved template ${body.template.template_key} v${body.version.version}.`]);
        return true;
      }
      showError("Save failed", ["Review the API response below."]);
      return false;
    }
    async function importTemplate() {
      clearBanners();
      importFile.value = "";
      importFile.click();
    }
    async function exportTemplate() {
      clearBanners();
      const parsed = parseJson(area.value);
      if (parsed.error) {
        showError("Export failed", ["Editor JSON is invalid.", "Fix the JSON syntax and try again."]);
        return;
      }
      const validationErrors = validateTemplatePayload(parsed.value);
      if (validationErrors.length) {
        showError("Export failed", validationErrors.concat(["Fix the schema issues above before exporting."]));
        return;
      }
      const schema = parsed.value.schema_json || {};
      const fileName = `${schema.template_key || "template"}-schema.json`;
      const jsonText = JSON.stringify(parsed.value, null, 2);
      const blob = new Blob([jsonText], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      showSuccess("Export successful", [`Downloaded ${fileName}.`]);
    }
    importFile.addEventListener("change", async (event) => {
      clearBanners();
      const file = event.target.files && event.target.files[0];
      if (!file) {
        showError("Import failed", ["No file selected."]);
        return;
      }
      let text = "";
      try {
        text = await file.text();
      } catch (err) {
        showError("Import failed", ["Could not read the selected file."]);
        return;
      }
      const parsed = parseJson(text);
      if (parsed.error) {
        showError("Import failed", ["File contents are not valid JSON.", "Fix the JSON file and re-import."]);
        return;
      }
      const validationErrors = validateTemplatePayload(parsed.value);
      if (validationErrors.length) {
        showError("Import failed", validationErrors.concat(["Fix the schema issues in the JSON file and try again."]));
        return;
      }
      const schema = parsed.value.schema_json || {};
      const sectionCount = Array.isArray(schema.discipline_repeat?.items)
        ? schema.discipline_repeat.items.length
        : 0;
      const confirmMessage = `Load schema "${schema.display_name}" (key: ${schema.template_key}) with ${sectionCount} sections?`;
      if (!window.confirm(confirmMessage)) {
        showError("Import cancelled", ["No changes were made."]);
        return;
      }
      area.value = JSON.stringify(parsed.value, null, 2);
      if (schema.template_key) {
        document.getElementById("templateKey").value = schema.template_key;
      }
      showSuccess("Import successful", [`Loaded ${file.name}.`]);
      show({ status: "imported", file: file.name, template_key: schema.template_key || null });
      const publishMessage = `Make this imported schema the new active version for "${schema.template_key}"?`;
      if (!window.confirm(publishMessage)) {
        return;
      }
      const publishOk = await savePayloadAsVersion(parsed.value, schema.template_key || document.getElementById("templateKey").value.trim(), "Import published");
      if (!publishOk) {
        showError("Publish failed", [
          "The imported schema was loaded, but it was not versioned.",
          "Review the API response and fix any validation issues, then try saving again."
        ]);
      }
    });
    loadAuthState();
    listVersions();
  </script>
</body>
</html>
"""


@router.get(
    "/dev/review-form",
    response_class=HTMLResponse,
    dependencies=[Depends(require_admin_access)],
)
async def review_form_page() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Reviewer Form Test</title>
  <style>
    body { font-family: "Segoe UI", sans-serif; margin: 24px; max-width: 1200px; }
    .card { border: 1px solid #ddd; border-radius: 6px; margin: 12px 0; padding: 12px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    textarea { width: 100%; min-height: 80px; }
    .muted { color: #666; font-size: 0.9rem; }
    pre { background: #f8f8f8; padding: 12px; white-space: pre-wrap; }
    .error-banner { border: 1px solid #b42318; background: #fef3f2; color: #7a271a; padding: 10px 12px; border-radius: 6px; margin: 12px 0; display: none; }
    .error-banner h3 { margin: 0 0 6px 0; font-size: 1rem; }
    .error-banner ul { margin: 0; padding-left: 18px; }
    .error-section { border-color: #b42318; box-shadow: 0 0 0 1px #b42318 inset; }
    .info-banner { border: 1px solid #0f766e; background: #ecfdf5; color: #115e59; padding: 10px 12px; border-radius: 6px; margin: 12px 0; display: none; }
  </style>
</head>
<body>
  <div style="margin-bottom:12px;">
    <a href="/dev/admin">Home</a> |
    <a href="/dev/user-access-admin">User Access Admin</a> |
    <a href="/dev/admin-form-templates">Template Manager</a> |
    <a href="/dev/active-forms-admin">Active Forms</a> |
    <a href="/dev/review-form">Reviewer Test Form</a> 
  </div>
  <h1>Reviewer Form (Dev)</h1>
  <div id="welcomeLine" style="margin: 6px 0 18px; font-weight: 600;"></div>
  <div class="card">
    <strong>Auth State:</strong>
    <pre id="authState" style="margin-top:8px;">Loading...</pre>
    <a href="/auth/login">Login</a>
    <button type="button" onclick="logout()">Logout</button>
  </div>
  <label>Review Request ID <input id="reviewRequestId" size="42" /></label>
  <button onclick="loadForm()">Load Form</button>
  <button onclick="validateForm()">Validate</button>
  <button onclick="submitForm()">Submit</button>
  <div id="validationBanner" class="error-banner"></div>
  <div id="infoBanner" class="info-banner"></div>
  <div id="brandHeader" class="card"></div>
  <div id="autoFields" class="card"></div>
  <div id="disciplineBlocks"></div>
  <h3>Result</h3>
  <pre id="result"></pre>
  <script>
    let context = null;
    let me = null;
    let sectionLabelToKey = new Map();
    function isInternalEmail(email) {
      return /@(greshamsmith\.com|gspnet\.com)$/i.test(email || "");
    }
    function extractFirstName(displayName, email) {
      const rawName = (displayName || "").trim();
      if (rawName) {
        const namePart = rawName.includes(",")
          ? rawName.split(",")[1]?.trim()
          : rawName;
        const token = (namePart || "").split(/\s+/)[0];
        if (token) {
          return token.charAt(0).toUpperCase() + token.slice(1).toLowerCase();
        }
      }
      const local = (email || "").split("@")[0];
      if (!local) return "";
      const firstPart = local.split(".")[0];
      if (!firstPart) return "";
      const cleaned = firstPart.replace(/[_-]+/g, " ").trim();
      if (!cleaned) return "";
      const token = cleaned.split(" ")[0];
      if (!token) return "";
      return token.charAt(0).toUpperCase() + token.slice(1).toLowerCase();
    }
    function setWelcome(body) {
      const welcome = document.getElementById("welcomeLine");
      if (!welcome) return;
      if (!body || body.auth_status !== "authenticated") {
        welcome.textContent = "";
        return;
      }
      const email = body.email || "";
      if (isInternalEmail(email)) {
        const first = extractFirstName(body.display_name, email);
        welcome.textContent = first ? `Welcome, ${first}` : "Welcome";
        return;
      }
      welcome.textContent = "Welcome";
    }
    function show(value) {
      document.getElementById("result").textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
    }
    async function loadAuthState() {
      const response = await fetch("/me");
      const body = await response.json();
      document.getElementById("authState").textContent = JSON.stringify(body, null, 2);
      me = body;
      setWelcome(body);
      if (body.effective_access_state !== "active") {
        setFormDisabled(true);
      }
    }
    async function logout() {
      await fetch("/auth/logout", { method: "POST" });
      await loadAuthState();
      setFormDisabled(true);
    }
    function hasPerm(key) {
      if (!me || !Array.isArray(me.permissions)) return false;
      return me.permissions.includes(key);
    }
    function clearValidationUi() {
      document.getElementById("validationBanner").style.display = "none";
      document.getElementById("validationBanner").innerHTML = "";
      document.getElementById("infoBanner").style.display = "none";
      document.getElementById("infoBanner").innerHTML = "";
      document.querySelectorAll(".error-section").forEach(el => el.classList.remove("error-section"));
    }
    function showInfo(message) {
      const banner = document.getElementById("infoBanner");
      banner.textContent = message;
      banner.style.display = "block";
    }
    function setFormDisabled(disabled) {
      const selector = "input, textarea, button";
      document.querySelectorAll(selector).forEach(el => {
        if (el.id === "reviewRequestId") return;
        if (el.getAttribute("onclick") === "loadForm()") return;
        el.disabled = disabled;
      });
    }
    function renderValidationErrors(errors) {
      if (!Array.isArray(errors) || errors.length === 0) return;
      const banner = document.getElementById("validationBanner");
      const items = errors.map(err => `<li>${err}</li>`).join("");
      banner.innerHTML = `<h3>Validation failed</h3><ul>${items}</ul>`;
      banner.style.display = "block";

      const pattern = /Section '([^']+)' for discipline '([^']+)'/;
      errors.forEach(err => {
        const match = err.match(pattern);
        if (!match) return;
        const sectionLabel = match[1];
        const disciplineName = match[2];
        const sectionKey = sectionLabelToKey.get(sectionLabel) || sectionLabel;
        const card = [...document.querySelectorAll("[data-discipline-id]")]
          .find(item => item.getAttribute("data-discipline-name") === disciplineName);
        if (!card) return;
        const section = card.querySelector(`[data-section="${sectionKey}"]`);
        if (section) section.classList.add("error-section");
      });
    }
    async function loadForm() {
      clearValidationUi();
      if (me && me.effective_access_state !== "active") {
        return show({ detail: "No active access. Sign in and request approval." });
      }
      const id = document.getElementById("reviewRequestId").value.trim();
      const response = await fetch(`/review-forms/${id}`);
      const body = await response.json();
      if (!response.ok) return show(body);
      context = body;
      sectionLabelToKey = new Map(
        (body.schema_json?.discipline_repeat?.items || []).map(item => [item.section_label, item.section_key])
      );
      const brand = body.schema_json.branding || {};
      const brandDiv = document.getElementById("brandHeader");
      const logoHtml = brand.logo_url ? `<img src="${brand.logo_url}" alt="logo" style="display:block;margin-bottom:8px;" />` : "";
      brandDiv.innerHTML = `${logoHtml}<div><strong>${brand.org_name || ""}</strong></div>`;
      const autoDiv = document.getElementById("autoFields");
      autoDiv.innerHTML = "<h3>Auto Fields</h3>" + Object.entries(body.auto_values).map(([k,v]) => `<div><strong>${k}</strong>: ${v ?? ""}</div>`).join("");
      const sections = body.schema_json.discipline_repeat.items;
      const blocks = body.disciplines.map((d, idx) => `
        <div class="card" data-discipline-id="${d.discipline_id}" data-discipline-name="${d.discipline_name}">
          <h3>${d.discipline_name}</h3>
          ${sections.map(s => `
            <div class="card" data-section="${s.section_key}">
              <div><strong>${s.section_label}</strong></div>
              <label><input type="radio" name="${idx}-${s.section_key}" value="complete"> Complete</label>
              <label><input type="radio" name="${idx}-${s.section_key}" value="na"> N/A</label>
              <div><label>Signature Name <input data-field="signature_name" /></label></div>
              <div class="muted">Must match reviewer name: ${body.reviewer_name}</div>
              <div><label>Signed At <input data-field="signed_at" readonly /></label> <button type="button" onclick="stamp(this)">Stamp</button></div>
              <div><label>Notes</label><textarea data-field="notes"></textarea></div>
            </div>
          `).join("")}
        </div>
      `).join("");
      document.getElementById("disciplineBlocks").innerHTML = blocks;
      setFormDisabled(false);
      if (body.status === "submitted") {
        showInfo("This review request has already been submitted and is locked.");
        setFormDisabled(true);
      }
      show(body);
    }
    function loadReviewRequestIdFromQuery() {
      const params = new URLSearchParams(window.location.search);
      const fromQuery = params.get("reviewRequestId") || params.get("review_request_id");
      if (fromQuery) {
        document.getElementById("reviewRequestId").value = fromQuery.trim();
      }
    }
    function stamp(button) {
      const section = button.closest("[data-section]");
      const field = section.querySelector("[data-field='signed_at']");
      field.value = new Date().toISOString();
    }
    function collectPayload() {
      const disciplineCards = [...document.querySelectorAll("[data-discipline-id]")];
      return {
        review_request_id: context.review_request_id,
        reviewer_name_expected: context.reviewer_name,
        discipline_responses: disciplineCards.map(card => {
          const sections = {};
          [...card.querySelectorAll("[data-section]")].forEach(section => {
            const sectionKey = section.getAttribute("data-section");
            const checked = section.querySelector("input[type='radio']:checked");
            const signatureRaw = section.querySelector("[data-field='signature_name']").value;
            const signedAtRaw = section.querySelector("[data-field='signed_at']").value;
            const signatureName = signatureRaw.trim() ? signatureRaw : null;
            const signedAt = signedAtRaw.trim() ? signedAtRaw : null;
            sections[sectionKey] = {
              status: checked ? checked.value : null,
              signature_name: signatureName,
              signed_at: signedAt,
              notes: section.querySelector("[data-field='notes']").value
            };
          });
          return {
            discipline_id: card.getAttribute("data-discipline-id"),
            discipline_name: card.getAttribute("data-discipline-name"),
            sections
          };
        })
      };
    }
    async function validateForm() {
      clearValidationUi();
      if (me && !hasPerm("reviewer.form.validate") && !hasPerm("admin.access")) {
        return show({ detail: "Read-only access cannot validate forms." });
      }
      if (context && context.status === "submitted") {
        showInfo("This review request has already been submitted and cannot be validated.");
        return;
      }
      const id = document.getElementById("reviewRequestId").value.trim();
      const response = await fetch(`/review-forms/${id}/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(collectPayload())
      });
      const body = await response.json();
      if (!response.ok) {
        show(body);
        return;
      }
      show(body);
      if (body && body.valid === false) {
        renderValidationErrors(body.errors);
      }
    }
    async function submitForm() {
      clearValidationUi();
      if (me && !hasPerm("reviewer.form.submit") && !hasPerm("admin.access")) {
        return show({ detail: "Read-only access cannot submit forms." });
      }
      if (context && context.status === "submitted") {
        showInfo("This review request has already been submitted and cannot be updated.");
        return;
      }
      const id = document.getElementById("reviewRequestId").value.trim();
      const response = await fetch(`/review-forms/${id}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(collectPayload())
      });
      const body = await response.json();
      show(body);
      if (!response.ok && body && Array.isArray(body.detail)) {
        renderValidationErrors(body.detail);
      } else if (!response.ok && response.status === 409) {
        showInfo(body?.detail || "This review request has already been submitted.");
      }
    }
    (async () => {
      await loadAuthState();
      loadReviewRequestIdFromQuery();
      if (document.getElementById("reviewRequestId").value.trim()) {
        await loadForm();
      }
    })();
  </script>
</body>
</html>
"""


@router.get(
    "/dev/active-forms-admin",
    response_class=HTMLResponse,
    dependencies=[Depends(require_active_review_requests_read)],
)
async def active_forms_admin_page() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Active Review Requests Admin</title>
  <style>
    body { font-family: "Segoe UI", sans-serif; margin: 24px; max-width: 1400px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; vertical-align: top; font-size: 0.9rem; }
    th { background: #f5f5f5; text-align: left; }
    input, select, button { margin-right: 6px; margin-bottom: 4px; }
    .toolbar { margin-bottom: 12px; }
    pre { background: #f8f8f8; padding: 12px; white-space: pre-wrap; }
  </style>
</head>
<body>
  <div style="margin-bottom:12px;">
    <a href="/dev/admin">Home</a> |
    <a href="/dev/user-access-admin">User Access Admin</a> |
    <a href="/dev/admin-form-templates">Template Manager</a> |
    <a href="/dev/active-forms-admin">Active Forms</a> |
    <a href="/dev/review-form">Reviewer Test Form</a> 
  </div>
  <div class="toolbar">
    <strong>Auth State:</strong>
    <pre id="authState" style="margin-top:8px;">Loading...</pre>
    <a href="/auth/login">Login</a>
    <button type="button" onclick="logout()">Logout</button>
  </div>
  <h1>Active Review Requests (Dev Admin)</h1>
  <div id="welcomeLine" style="margin: 6px 0 18px; font-weight: 600;"></div>
  <div class="toolbar">
    <button onclick="loadActiveRequests()">Refresh Active Requests</button>
  </div>
  <div id="tableWrap"></div>
  <h3>Result</h3>
  <pre id="result"></pre>
  <script>
    const result = document.getElementById("result");
    const authState = document.getElementById("authState");
    let isAdmin = false;
    function isInternalEmail(email) {
      return /@(greshamsmith\.com|gspnet\.com)$/i.test(email || "");
    }
    function extractFirstName(displayName, email) {
      const rawName = (displayName || "").trim();
      if (rawName) {
        const namePart = rawName.includes(",")
          ? rawName.split(",")[1]?.trim()
          : rawName;
        const token = (namePart || "").split(/\s+/)[0];
        if (token) {
          return token.charAt(0).toUpperCase() + token.slice(1).toLowerCase();
        }
      }
      const local = (email || "").split("@")[0];
      if (!local) return "";
      const firstPart = local.split(".")[0];
      if (!firstPart) return "";
      const cleaned = firstPart.replace(/[_-]+/g, " ").trim();
      if (!cleaned) return "";
      const token = cleaned.split(" ")[0];
      if (!token) return "";
      return token.charAt(0).toUpperCase() + token.slice(1).toLowerCase();
    }
    function setWelcome(body) {
      const welcome = document.getElementById("welcomeLine");
      if (!welcome) return;
      if (!body || body.auth_status !== "authenticated") {
        welcome.textContent = "";
        return;
      }
      const email = body.email || "";
      if (isInternalEmail(email)) {
        const first = extractFirstName(body.display_name, email);
        welcome.textContent = first ? `Welcome, ${first}` : "Welcome";
        return;
      }
      welcome.textContent = "Welcome";
    }
    function show(value) {
      result.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
    }
    async function apiFetch(url, options = null) {
      const response = await fetch(url, options || undefined);
      const body = await response.json();
      if (response.status === 401) {
        show({ detail: "Unauthenticated. Use /auth/login first." });
      }
      return { response, body };
    }
    async function loadAuthState() {
      const { response, body } = await apiFetch("/me");
      if (!response.ok) return;
      authState.textContent = JSON.stringify(body, null, 2);
      setWelcome(body);
      const perms = Array.isArray(body.permissions) ? body.permissions : [];
      isAdmin = perms.includes("admin.access");
    }
    async function logout() {
      await fetch("/auth/logout", { method: "POST" });
      await loadAuthState();
    }
    async function getVersions(templateKey) {
      const { response, body } = await apiFetch(`/admin/form-templates/${encodeURIComponent(templateKey)}/versions`);
      if (!response.ok || !Array.isArray(body)) return [];
      return body.sort((a, b) => Number(b.version) - Number(a.version));
    }
    async function loadActiveRequests() {
      const { response, body } = await apiFetch("/admin/review-requests/active");
      if (!response.ok) {
        document.getElementById("tableWrap").innerHTML = "";
        return show(body);
      }
      if (!Array.isArray(body) || body.length === 0) {
        document.getElementById("tableWrap").innerHTML = "<div>No active review requests found.</div>";
        return;
      }
      const rows = await Promise.all(body.map(async (item) => {
        const versions = await getVersions(item.template_key);
        const versionOptions = versions.map(v => {
          const selected = Number(v.version) === Number(item.expected_form_version) ? "selected" : "";
          const activeLabel = v.is_active ? " (active)" : "";
          return `<option value="${v.version}" ${selected}>v${v.version}${activeLabel}</option>`;
        }).join("") || `<option value="${item.expected_form_version}">v${item.expected_form_version}</option>`;
        return `
          <tr data-request-id="${item.review_request_id}">
            <td><a href="/dev/review-form?reviewRequestId=${item.review_request_id}">${item.review_request_id}</a></td>
            <td>${item.status}</td>
            <td>${item.reviewer_name || ""}<br>${item.reviewer_email || ""}</td>
            <td>${item.project_number || ""}<br>${item.project_name || ""}</td>
            <td>${item.submittal_name || ""}<br>${item.submittal_date || ""}</td>
            <td>${item.template_key}<br>current: v${item.expected_form_version}<br>active: ${item.active_template_version ? "v" + item.active_template_version : "-"}</td>
            <td>${item.discipline_count}</td>
            <td>${item.updated_at}</td>
            <td ${isAdmin ? "" : "style='display:none;'"} data-admin-col="true">
              <div><input data-role="template-key" value="${item.template_key}" /></div>
              <div><button type="button" onclick="reloadVersions(this)">Load Versions</button></div>
              <div><select data-role="version-select">${versionOptions}</select></div>
              <div><button type="button" onclick="reassignTemplate(this)">Reassign</button></div>
              <hr />
              <div><input data-role="reviewer-email" value="${item.reviewer_email || ""}" placeholder="new reviewer email" /></div>
              <div><button type="button" onclick="reassignReviewer(this)">Reassign Reviewer</button></div>
            </td>
          </tr>
        `;
      }));
      document.getElementById("tableWrap").innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Review Request ID</th>
              <th>Status</th>
              <th>Reviewer</th>
              <th>Project</th>
              <th>Submittal</th>
              <th>Template</th>
              <th>Disciplines</th>
              <th>Updated</th>
              <th ${isAdmin ? "" : "style='display:none;'"} data-admin-col="true">Admin Actions</th>
            </tr>
          </thead>
          <tbody>${rows.join("")}</tbody>
        </table>
      `;
      show(body);
    }
    async function reloadVersions(button) {
      const row = button.closest("tr");
      const key = row.querySelector("[data-role='template-key']").value.trim();
      const select = row.querySelector("[data-role='version-select']");
      const versions = await getVersions(key);
      if (!versions.length) {
        select.innerHTML = '<option value="">No versions found</option>';
        return;
      }
      select.innerHTML = versions.map(v => {
        const activeLabel = v.is_active ? " (active)" : "";
        return `<option value="${v.version}">v${v.version}${activeLabel}</option>`;
      }).join("");
    }
    async function reassignTemplate(button) {
      if (!isAdmin) {
        return show({ detail: "Forbidden" });
      }
      const row = button.closest("tr");
      const reviewRequestId = row.getAttribute("data-request-id");
      const templateKey = row.querySelector("[data-role='template-key']").value.trim();
      const version = Number(row.querySelector("[data-role='version-select']").value);
      const { response, body } = await apiFetch(`/admin/review-requests/${reviewRequestId}/reassign-template`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ template_key: templateKey, version })
      });
      show(body);
      if (response.ok) {
        await loadActiveRequests();
      }
    }
    async function reassignReviewer(button) {
      if (!isAdmin) {
        return show({ detail: "Forbidden" });
      }
      const row = button.closest("tr");
      const reviewRequestId = row.getAttribute("data-request-id");
      const reviewerEmail = row.querySelector("[data-role='reviewer-email']").value.trim();
      if (!reviewerEmail) {
        return show({ detail: "Provide reviewer email" });
      }
      const { response, body } = await apiFetch(`/admin/review-requests/${reviewRequestId}/reassign-reviewer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reviewer_email: reviewerEmail })
      });
      show(body);
      if (response.ok) {
        await loadActiveRequests();
      }
    }
    (async () => {
      await loadAuthState();
      await loadActiveRequests();
    })();
  </script>
</body>
</html>
"""
