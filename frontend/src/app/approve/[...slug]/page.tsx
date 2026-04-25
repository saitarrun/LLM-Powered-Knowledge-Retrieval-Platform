"use client";

import { useState, use } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, XCircle, Shield, Loader2, Lock, ArrowRight } from "lucide-react";

function ApproveContent({ params }: { params: { slug: string[] } }) {
  const [status, setStatus] = useState<"pending" | "approved" | "rejected">("pending");
  const [loading, setLoading] = useState(false);

  const handleAction = async (action: "approve" | "reject") => {
    setLoading(true);
    try {
      // Proxy to n8n webhook
      const res = await fetch(`/n8n-proxy/approve/${params.slug.join("/")}?action=${action}`, {
        method: "POST"
      });
      if (res.ok) {
        setStatus(action === "approve" ? "approved" : "rejected");
      }
    } catch (err) {
      console.error("Action failed:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#fbf9f7] flex flex-col items-center justify-center p-8 selection:bg-[#ff7a59]/10">
      <AnimatePresence mode="wait">
        {status === "pending" ? (
          <motion.div 
            key="pending"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.05 }}
            className="w-full max-w-2xl"
          >
            <div className="bg-white rounded-[4rem] border border-slate-100 shadow-premium overflow-hidden">
              <div className="p-16 space-y-12">
                <div className="flex justify-between items-start">
                   <div className="w-20 h-20 bg-slate-50 rounded-[2.5rem] flex items-center justify-center border border-slate-100">
                      <Shield size={32} className="text-slate-900" />
                   </div>
                   <div className="px-6 py-2 bg-amber-50 rounded-full border border-amber-100">
                      <span className="text-xs font-black text-amber-600 tracking-[0.3em] uppercase">Auth Required</span>
                   </div>
                </div>

                <div className="space-y-6">
                  <h1 className="text-6xl font-black text-slate-900 tracking-tighter leading-[0.9]">
                    Document <br /> Ingestion.
                  </h1>
                  <p className="text-xl text-slate-500 font-medium leading-relaxed max-w-md">
                    Enterprise security protocol requires explicit authorization for this ingestion payload.
                  </p>
                </div>

                <div className="pt-8 flex flex-col sm:flex-row gap-6">
                  <button 
                    disabled={loading}
                    onClick={() => handleAction("approve")}
                    className="group relative h-20 flex-1 bg-slate-900 rounded-[2rem] overflow-hidden transition-all active:scale-[0.98] disabled:opacity-50"
                  >
                    <div className="absolute inset-0 bg-gradient-to-tr from-emerald-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                    <div className="relative flex items-center justify-center gap-3">
                      {loading ? <Loader2 size={24} className="animate-spin text-white" /> : (
                        <>
                          <span className="text-xl font-black text-white tracking-tight">Approve Access</span>
                          <ArrowRight size={24} className="text-white/40 group-hover:translate-x-1 transition-transform" />
                        </>
                      )}
                    </div>
                  </button>

                  <button 
                    disabled={loading}
                    onClick={() => handleAction("reject")}
                    className="h-20 flex-1 bg-white border-2 border-slate-100 rounded-[2rem] hover:bg-slate-50 transition-all active:scale-[0.98] disabled:opacity-50 flex items-center justify-center"
                  >
                    <span className="text-xl font-black text-slate-400 tracking-tight">Purge Data</span>
                  </button>
                </div>
              </div>
              
              <div className="bg-slate-50/50 p-8 border-t border-slate-100 flex items-center justify-center gap-3">
                <Lock size={14} className="text-slate-300" />
                <span className="text-[10px] font-bold text-slate-400 tracking-[0.5em] uppercase">Secure Enterprise Gateway</span>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-2xl"
          >
            <AnimatePresence mode="wait">
              {status === "approved" ? (
                <motion.div 
                  key="approved"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ type: "spring", bounce: 0.4, duration: 0.8 }}
                  className="bg-white rounded-[4rem] border border-slate-100 shadow-premium overflow-hidden text-center"
                >
                  <div className="p-20 space-y-10">
                    <div className="flex justify-center">
                       <motion.div 
                         initial={{ scale: 0 }}
                         animate={{ scale: 1 }}
                         transition={{ delay: 0.2, type: "spring", bounce: 0.6 }}
                         className="w-32 h-32 bg-emerald-50 rounded-full flex items-center justify-center border-4 border-emerald-100"
                       >
                         <CheckCircle size={64} className="text-emerald-500" />
                       </motion.div>
                    </div>
                    <div className="space-y-4">
                      <h1 className="text-4xl font-black text-slate-900 tracking-tighter">Authorization Successful</h1>
                      <p className="text-base text-slate-500 font-medium tracking-tight">The document has been securely routed to the vector indexing pipeline.</p>
                    </div>
                    <button onClick={() => window.close()} className="btn-secondary px-12 py-5 rounded-full mt-4">Close Window</button>
                  </div>
                </motion.div>
              ) : (
                <motion.div 
                  key="rejected"
                  initial={{ opacity: 0, scale: 0.9, rotate: -5 }}
                  animate={{ opacity: 1, scale: 1, rotate: 0 }}
                  transition={{ type: "spring", bounce: 0.4, duration: 0.8 }}
                  className="bg-white rounded-[4rem] border border-slate-100 shadow-premium overflow-hidden text-center"
                >
                  <div className="p-20 space-y-10">
                    <div className="flex justify-center">
                       <motion.div 
                         initial={{ scale: 0 }}
                         animate={{ scale: 1 }}
                         transition={{ delay: 0.2, type: "spring", bounce: 0.6 }}
                         className="w-32 h-32 bg-red-50 rounded-[3rem] flex items-center justify-center border-4 border-red-100 rotate-12"
                       >
                         <XCircle size={64} className="text-red-500" />
                       </motion.div>
                    </div>
                    <div className="space-y-4">
                      <h1 className="text-4xl font-black text-slate-900 tracking-tighter">Ingestion Rejected</h1>
                      <p className="text-base text-slate-500 font-medium tracking-tight">The document payload has been purged from temporary storage.</p>
                    </div>
                    <button onClick={() => window.close()} className="btn-secondary px-12 py-5 rounded-full mt-4">Close Window</button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function ApprovePage({
  params,
}: {
  params: Promise<{ slug: string[] }>;
}) {
  const resolvedParams = use(params);

  return <ApproveContent params={resolvedParams} />;
}
