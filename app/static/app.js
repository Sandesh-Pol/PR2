const recipients = document.querySelector('#recipients');
const form = document.querySelector('#job-form');
const message = document.querySelector('#form-message');
let activeJob;

function addRecipient() {
  const row = document.createElement('div');
  row.className = 'grid gap-2 rounded-lg bg-stone-50 p-3 sm:grid-cols-2';
  row.innerHTML = '<input required name="recipient_name" placeholder="Full name" class="field mt-0"><input required type="email" name="recipient_email" placeholder="Email" class="field mt-0"><input required name="course" placeholder="Course" class="field mt-0"><input required type="date" name="completion_date" class="field mt-0"><button type="button" class="remove text-left text-xs font-semibold text-slate-500 sm:col-span-2">Remove recipient</button>';
  row.querySelector('.remove').onclick = () => row.remove();
  recipients.append(row);
}

document.querySelector('#add-recipient').onclick = addRecipient;
addRecipient();

form.onsubmit = async (event) => {
  event.preventDefault();
  const data = new FormData(form);
  const names = data.getAll('recipient_name');
  const emails = data.getAll('recipient_email');
  const courses = data.getAll('course');
  const dates = data.getAll('completion_date');
  const payload = { title: data.get('title'), issuer: data.get('issuer'), issue_date: data.get('issue_date'), recipients: names.map((name, i) => ({ name, email: emails[i], course: courses[i], completion_date: dates[i] })) };
  const response = await fetch('/api/jobs', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
  if (!response.ok) { message.textContent = (await response.json()).detail || 'Could not create job.'; return; }
  activeJob = await response.json(); message.textContent = 'Generation started.'; render(activeJob); poll();
};

async function poll() {
  if (!activeJob || ['completed', 'partial', 'failed'].includes(activeJob.status)) return;
  await new Promise(resolve => setTimeout(resolve, 500));
  activeJob = await (await fetch(`/api/jobs/${activeJob.id}`)).json(); render(activeJob); poll();
}
function render(job) {
  document.querySelector('#job-status').textContent = job.status;
  document.querySelector('#job-summary').innerHTML = [['Total', job.total], ['Ready', job.succeeded], ['Failed', job.failed]].map(([label, value]) => `<div class="rounded-lg bg-slate-800 p-4"><div class="text-2xl font-semibold">${value}</div><div class="text-xs text-slate-400">${label}</div></div>`).join('');
  document.querySelector('#results').innerHTML = job.certificates.map(item => `<div class="flex items-center justify-between rounded-lg bg-slate-800 px-4 py-3"><div><div class="font-semibold">${item.recipient_name}</div><div class="text-xs text-slate-400">${item.course}</div></div>${item.download_url ? `<a class="text-sm font-semibold text-orange-300" href="${item.download_url}">Download</a>` : `<span class="text-xs text-red-300">${item.error_message || item.status}</span>`}</div>`).join('');
}
