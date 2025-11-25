// src/pages/EmailDetail.jsx
import React, { useEffect, useState } from "react";
import { api } from "../lib/api";

export default function EmailDetail({ emailId }) {
  const [emailData, setEmailData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (emailId) fetchEmail(emailId);
    else setEmailData(null);
    // eslint-disable-next-line
  }, [emailId]);

  async function fetchEmail(id) {
    try {
      setLoading(true);
      const res = await api.get(`/email/${id}`);
      setEmailData(res.data);
    } catch (e) {
      console.error(e);
      setEmailData(null);
    } finally {
      setLoading(false);
    }
  }

  if (!emailId) {
    return <div className="text-sm text-neutral-400">Select an email to view details.</div>;
  }

  if (loading) return <div className="text-sm text-neutral-400">Loading email...</div>;
  if (!emailData) return <div className="text-sm text-red-500">Email not found.</div>;

  const { email, processing } = emailData;
  let tasks = [];
  try {
    if (processing && processing.tasks_json) {
      tasks = JSON.parse(processing.tasks_json);
    }
  } catch (e) {
    tasks = [];
  }

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-2xl p-4">
      <div className="mb-3">
        <div className="text-lg font-semibold">{email.subject}</div>
        <div className="text-xs text-neutral-400">{email.sender} • {new Date(email.timestamp).toLocaleString()}</div>
      </div>

      <div className="mb-6 whitespace-pre-wrap text-sm text-neutral-200 leading-relaxed">{email.body}</div>

      <div>
        <h4 className="font-semibold mb-3">Extracted Tasks</h4>
        {tasks.length === 0 && <div className="text-sm text-neutral-500">No tasks found.</div>}
        {tasks.map((t, i) => (
          <div key={i} className="p-3 border border-neutral-800 rounded-lg mb-3 bg-neutral-850">
            <div className="font-medium">{t.task || t.description || "Task"}</div>
            {t.deadline && <div className="text-xs text-neutral-400 mt-1">Due: {t.deadline}</div>}
            {t.notes && <div className="text-sm text-neutral-200 mt-2">{t.notes}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}
