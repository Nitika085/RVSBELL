const state = {
  invoices: [],
  sortKey: null,
  sortAsc: true,
  selectedInvoiceId: null,
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

async function fetchJSON(url){
  const res = await fetch(url);
  return res.json();
}

function buildQuery(){
  const params = new URLSearchParams();
  const cust = $('#customerFilter').value;
  const s = $('#startDate').value;
  const e = $('#endDate').value;
  if(cust) params.set('customer_id', cust);
  if(s) params.set('start_date', s);
  if(e) params.set('end_date', e);
  return params.toString() ? '?' + params.toString() : '';
}

async function loadCustomers(){
  const customers = await fetchJSON('/customers');
  const select = $('#customerFilter');
  customers.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.customer_id;
    opt.textContent = c.name;
    select.appendChild(opt);
  });
}

function renderKPIs(kpi){
  $('#kpiInvoiced').textContent = kpi.total_invoiced.toFixed(2);
  $('#kpiReceived').textContent = kpi.total_received.toFixed(2);
  $('#kpiOutstanding').textContent = kpi.total_outstanding.toFixed(2);
  $('#kpiOverdue').textContent = kpi.percent_overdue.toFixed(2) + '%';
}

function renderTable(){
  const tbody = $('#invoiceTable tbody');
  tbody.innerHTML = '';
  // simple search
  const query = $('#search').value.trim().toLowerCase();
  let rows = state.invoices.filter(r => {
    const hay = `${r.invoice_id} ${r.customer_name}`.toLowerCase();
    return hay.includes(query);
  });
  // sort
  if(state.sortKey){
    rows.sort((a,b)=>{
      const x = a[state.sortKey];
      const y = b[state.sortKey];
      if(x === y) return 0;
      return (x > y ? 1 : -1) * (state.sortAsc ? 1 : -1);
    });
  }
  rows.forEach(r => {
    const tr = document.createElement('tr');
    if(r.aging_bucket !== 'Current' && Number(r.outstanding) > 0){
      tr.classList.add('overdue');
    }
    tr.innerHTML = `
      <td>${r.invoice_id}</td>
      <td>${r.customer_name}</td>
      <td>${r.invoice_date}</td>
      <td>${r.due_date}</td>
      <td>${Number(r.amount).toFixed(2)}</td>
      <td>${Number(r.total_paid).toFixed(2)}</td>
      <td>${Number(r.outstanding).toFixed(2)}</td>
      <td>${r.aging_bucket}</td>
      <td><button class="pay" data-id="${r.invoice_id}">Record Payment</button></td>
    `;
    tbody.appendChild(tr);
  });
}

let chart;
function renderChart(data){
  const labels = data.map(x=>x.name);
  const values = data.map(x=>Number(x.total_outstanding));
  const ctx = document.getElementById('top5Chart');
  if(chart){ chart.destroy(); }
  chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Outstanding',
        data: values,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: true } }
    }
  });
}

async function refreshAll(){
  const q = buildQuery();
  const [invoices, kpi, top5] = await Promise.all([
    fetchJSON('/invoices'+q),
    fetchJSON('/kpis'+q),
    fetchJSON('/top5')
  ]);
  state.invoices = invoices;
  renderKPIs(kpi);
  renderTable();
  renderChart(top5);
}

function attachEvents(){
  $('#applyFilters').addEventListener('click', refreshAll);
  $('#resetFilters').addEventListener('click', ()=>{
    $('#customerFilter').value='';
    $('#startDate').value='';
    $('#endDate').value='';
    $('#search').value='';
    refreshAll();
  });
  $('#search').addEventListener('input', renderTable);

  // column sorting
  $$('#invoiceTable th[data-sort]').forEach(th=>{
    th.addEventListener('click', ()=>{
      const key = th.getAttribute('data-sort');
      if(state.sortKey === key) state.sortAsc = !state.sortAsc;
      else { state.sortKey = key; state.sortAsc = true; }
      renderTable();
    });
  });

  // record payment click
  $('#invoiceTable').addEventListener('click', (e)=>{
    const btn = e.target.closest('button.pay');
    if(!btn) return;
    state.selectedInvoiceId = btn.getAttribute('data-id');
    $('#modalInvoiceId').textContent = state.selectedInvoiceId;
    $('#paymentAmount').value = '';
    $('#paymentDate').valueAsDate = new Date();
    $('#modal').classList.remove('hidden');
  });

  $('#cancelPayment').addEventListener('click', ()=> $('#modal').classList.add('hidden'));
  $('#savePayment').addEventListener('click', async ()=>{
    const amount = parseFloat($('#paymentAmount').value);
    const date = $('#paymentDate').value;
    if(!amount || !date){
      alert('Enter amount and date');
      return;
    }
    const res = await fetch('/payments', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ invoice_id: Number(state.selectedInvoiceId), amount, payment_date: date })
    });
    if(!res.ok){
      const err = await res.json();
      alert('Error: ' + (err.error || res.statusText));
    }else{
      $('#modal').classList.add('hidden');
      await refreshAll();
    }
  });
}

(async function init(){
  await loadCustomers();
  attachEvents();
  await refreshAll();
})();
