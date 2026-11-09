let chart = null;
let allTransactions = [];
const money = value => new Intl.NumberFormat("en-IN", {style:"currency", currency:"INR", maximumFractionDigits:2}).format(value || 0);
const $ = id => document.getElementById(id);

async function api(url, options={}) {
  const response = await fetch(url, {headers:{"Content-Type":"application/json"}, ...options});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}

async function refresh() {
  try {
    const [transactions, summary, insights] = await Promise.all([
      api("/api/transactions"), api("/api/summary"), api("/api/insights")
    ]);
    allTransactions = transactions;
    $("balance").textContent = money(summary.balance);
    $("income").textContent = money(summary.income);
    $("expenses").textContent = money(summary.expenses);
    $("month-expenses").textContent = money(summary.month_expenses);
    renderTransactions(transactions.slice(0, 8));
    renderChart(summary.by_category);
    $("insight-list").innerHTML = insights.map(item => `<div class="insight-item">${escapeHtml(item)}</div>`).join("");
  } catch (error) {
    $("insight-list").innerHTML = `<p class="muted">${escapeHtml(error.message)}</p>`;
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[char]));
}

function renderTransactions(items) {
  const body = $("transaction-body");
  body.innerHTML = items.map(t => `
    <tr>
      <td>${escapeHtml(t.title)}<br><span style="font-size:10px;color:#a0a7b5;font-weight:400">${escapeHtml(t.note || "")}</span></td>
      <td><span class="type-tag">${escapeHtml(t.category)}</span></td>
      <td>${escapeHtml(t.txn_date)}</td>
      <td class="${t.kind === "income" ? "amount-income" : "amount-expense"}">${t.kind === "income" ? "+" : "−"}${money(t.amount)}</td>
      <td><button class="action-btn" data-edit="${t.id}">Edit</button><button class="action-btn delete-btn" data-delete="${t.id}">Delete</button></td>
    </tr>`).join("");
  $("no-transactions").style.display = items.length ? "none" : "block";
}

function renderChart(data) {
  const labels = Object.keys(data || {});
  $("chart-empty").style.display = labels.length ? "none" : "flex";
  if (chart) chart.destroy();
  if (!labels.length) return;
  chart = new Chart($("categoryChart"), {
    type:"doughnut",
    data:{labels, datasets:[{data:labels.map(label=>data[label]), backgroundColor:["#6b5ce7","#36b58b","#f2a45d","#5b9de4","#e47c9b","#9b83d7","#e3c45c","#8d9aaa"], borderWidth:0, hoverOffset:5}]},
    options:{responsive:true, maintainAspectRatio:false, cutout:"68%", plugins:{legend:{position:"right", labels:{usePointStyle:true,boxWidth:7,padding:15,font:{size:10}}}}}
  });
}

function openModal(transaction=null) {
  $("transaction-form").reset();
  $("transaction-id").value = transaction?.id || "";
  $("form-title").textContent = transaction ? "Edit transaction" : "Add transaction";
  $("title").value = transaction?.title || "";
  $("amount").value = transaction?.amount || "";
  $("kind").value = transaction?.kind || "expense";
  $("category").value = transaction?.category || "Food";
  $("txn-date").value = transaction?.txn_date || new Date().toISOString().slice(0,10);
  $("note").value = transaction?.note || "";
  $("form-error").textContent = "";
  $("modal").classList.add("show");
}
function closeModal(){ $("modal").classList.remove("show"); }

$("open-form").addEventListener("click", ()=>openModal());
$("close-form").addEventListener("click", closeModal);
$("modal").addEventListener("click", e=>{if(e.target === $("modal")) closeModal();});
$("view-all").addEventListener("click", ()=>renderTransactions(allTransactions));

$("transaction-form").addEventListener("submit", async event=>{
  event.preventDefault();
  const id = $("transaction-id").value;
  const payload = {
    title:$("title").value.trim(), amount:$("amount").value, kind:$("kind").value,
    category:$("category").value, txn_date:$("txn-date").value, note:$("note").value.trim()
  };
  try {
    await api(id ? `/api/transactions/${id}` : "/api/transactions", {
      method:id ? "PUT" : "POST", body:JSON.stringify(payload)
    });
    closeModal(); await refresh();
  } catch(error) { $("form-error").textContent = error.message; }
});

$("transaction-body").addEventListener("click", async event=>{
  const editId = event.target.dataset.edit;
  const deleteId = event.target.dataset.delete;
  if(editId) {
    const item = allTransactions.find(t=>t.id === Number(editId));
    if(item) openModal(item);
  }
  if(deleteId && confirm("Delete this transaction?")) {
    try { await api(`/api/transactions/${deleteId}`, {method:"DELETE"}); await refresh(); }
    catch(error) { alert(error.message); }
  }
});

refresh();
