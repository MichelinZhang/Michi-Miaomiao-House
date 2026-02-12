import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useSpring, useTransform, Reorder } from 'framer-motion';
import { 
  Play, Pause, Square, Settings, Activity, 
  Gauge, Terminal, LayoutDashboard, FileText, Gamepad2, 
  Plus, Trash2, Save, Upload, MoveVertical, Clock, 
  ChevronUp, ChevronDown, Move, RotateCcw, Zap, 
  Wifi, WifiOff, RefreshCw, Edit2, Lock, FileType
} from 'lucide-react';

// --- 配置与常量 ---
const COLORS = {
  bg: '#09090b', 
  panelBg: 'rgba(24, 24, 27, 0.4)',
  primary: '#3b82f6', // Blue (A)
  secondary: '#22c55e', // Green (B)
  accent: '#f97316', 
  danger: '#ef4444', 
  text: '#FFFFFF',
  border: 'rgba(255, 255, 255, 0.08)'
};

const INITIAL_SEQUENCE = [
  { id: '1', type: "MOVE_A", pos: 30.0, speed: 50.0, force: 100.0 },
  { id: '2', type: "DELAY", time: 1.0 },
  { id: '3', type: "MOVE_A", pos: 0.0, speed: 50.0, force: 100.0 },
  { id: '4', type: "MOVE_B", pos: 30.0, speed: 50.0, force: 100.0 },
  { id: '5', type: "DELAY", time: 1.0 },
  { id: '6', type: "MOVE_B", pos: 0.0, speed: 50.0, force: 100.0 },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('monitor'); 
  
  // 改进 1: 状态机管理 (IDLE, RUNNING, PAUSED)
  const [runState, setRunState] = useState('IDLE'); 
  
  const [isConnected, setIsConnected] = useState(false); 
  const [currentStepIdx, setCurrentStepIdx] = useState(-1);
  const [cycleCount, setCycleCount] = useState({ current: 0, total: 1000 });
  const [isEditingCycles, setIsEditingCycles] = useState(false); 
  const [editTotalInput, setEditTotalInput] = useState(1000);

  // 改进 2: 文件名绑定
  const [fileName, setFileName] = useState("sequence_01");

  // 核心状态
  const [cylA, setCylA] = useState({ pos: 0, target: 0, force: 0, force_out: 0 });
  const [cylB, setCylB] = useState({ pos: 0, target: 0, force: 0, force_out: 0 });
  const [sequence, setSequence] = useState(INITIAL_SEQUENCE);
  const [logs, setLogs] = useState(["System initialized.", "Ready."]);
  
  // 历史数据用于曲线图
  const [historyA, setHistoryA] = useState(new Array(60).fill(0));
  const [historyB, setHistoryB] = useState(new Array(60).fill(0));

  // 改进 3: 编辑锁 (运行时或暂停时禁止编辑)
  const isLocked = runState !== 'IDLE';

  // --- 连接检查与初始化 ---
  useEffect(() => {
    if (window.pywebview) {
      setIsConnected(true);
      window.addLog("Backend detected.");
    }
  }, []);

  // --- 模拟后台 Worker & 数据生成 ---
  useEffect(() => {
    let interval;
    // 只有在 RUNNING 状态下才执行逻辑
    if (runState === 'RUNNING') {
      interval = setInterval(() => {
        // 模拟运动与受力逻辑
        const updateCyl = (prev) => {
           const target = prev.target !== undefined ? prev.target : 0;
           const diff = target - prev.pos;
           
           // 模拟速度
           const step = diff * 0.15; 
           
           const newPos = Math.abs(diff) < 0.1 ? target : prev.pos + step;
           const baseNoise = Math.random() * 1.5; 
           
           let newForce = 0;
           if (Math.abs(diff) > 5) {
             newForce = 45 + Math.random() * 10;
           } else if (Math.abs(diff) > 0.1) {
             newForce = 20 + Math.random() * 5;
           } else {
             newForce = baseNoise;
           }
           
           const newForceOut = Math.abs(diff) > 0.5 ? (80 + Math.random() * 10) : 0;
           
           return { 
             ...prev, 
             pos: newPos, 
             force: newForce, 
             force_out: newForceOut
           };
        };
        
        setCylA(prev => updateCyl(prev));
        setCylB(prev => updateCyl(prev));

        setHistoryA(prev => [...prev.slice(1), cylA.force]);
        setHistoryB(prev => [...prev.slice(1), cylB.force]);

        if (Math.random() > 0.95) {
          setCurrentStepIdx(prev => {
             const next = (prev + 1) % sequence.length;
             const step = sequence[next];
             setLogs(l => {
                 const msg = `[STEP ${next+1}] ${step.type} Executing...`;
                 if (l[0] === msg) return l;
                 return [msg, ...l].slice(0, 20);
             });
             return next;
          });
        }
      }, 50); 
    }
    return () => clearInterval(interval);
  }, [runState, sequence, cylA.force, cylB.force]); // 依赖项改为 runState

  // 监听步骤变化
  useEffect(() => {
    if (currentStepIdx >= 0 && currentStepIdx < sequence.length) {
      const step = sequence[currentStepIdx];
      if (step.type === 'MOVE_A') setCylA(p => ({ ...p, target: step.pos }));
      if (step.type === 'MOVE_B') setCylB(p => ({ ...p, target: step.pos }));
      if (currentStepIdx === 0) setCycleCount(c => ({...c, current: c.current + 1}));
    }
  }, [currentStepIdx]);

  // --- 交互逻辑 ---
  const handleToggleConnection = () => {
    if (isConnected) {
       setIsConnected(false);
       setLogs(l => ["Disconnected from backend manually.", ...l]);
    } else {
       setLogs(l => ["Attempting connection...", ...l]);
       setTimeout(() => {
         setIsConnected(true);
         setLogs(l => ["Connection established.", ...l]);
       }, 800);
    }
  };

  // 改进 2: 保存逻辑包含文件名
  const handleSave = () => {
    const payload = {
        name: fileName,
        data: sequence
    };
    const json = JSON.stringify(payload);
    if(window.pywebview) window.pywebview.api.save_sequence(json);
    setLogs(l => [`Saved "${fileName}.json" (${sequence.length} steps).`, ...l]);
  };

  const handleLoad = () => {
    if (isLocked) return; // 运行时禁止加载
    if(window.pywebview) window.pywebview.api.load_sequence();
    setLogs(l => [`Sequence loaded.`, ...l]);
  };

  const handleCycleSubmit = () => {
    setCycleCount(prev => ({ ...prev, total: parseInt(editTotalInput) || 1000 }));
    setIsEditingCycles(false);
  };

  // 改进 1: 控制逻辑
  const handleStart = () => setRunState('RUNNING');
  const handlePause = () => {
      setRunState('PAUSED');
      setLogs(l => ["System Paused.", ...l]);
  };
  const handleStop = () => {
      setRunState('IDLE');
      setCurrentStepIdx(-1);
      setLogs(l => ["System Stopped.", ...l]);
  };
  const handleReset = () => {
      setRunState('IDLE');
      setCurrentStepIdx(-1);
      setCylA(p => ({ ...p, pos: 0, target: 0, force: 0, force_out: 0 }));
      setCylB(p => ({ ...p, pos: 0, target: 0, force: 0, force_out: 0 }));
      setCycleCount(c => ({ ...c, current: 0 }));
      setLogs(l => ["System Reset Complete.", ...l]);
  };

  return (
    <div className="w-full h-screen bg-neutral-950 text-white font-sans flex overflow-hidden selection:bg-blue-500/30">
      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 4px; }
        .no-scrollbar::-webkit-scrollbar { display: none; }
      `}</style>

      {/* 左侧导航 */}
      <nav className="w-16 lg:w-20 border-r border-white/5 bg-neutral-900/50 flex flex-col items-center py-4 lg:py-6 z-20 backdrop-blur-md relative shrink-0">
        <div className="mb-6 lg:mb-8 relative group">
          <div className="relative w-8 h-8 lg:w-10 lg:h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Activity className="text-white" size={20} />
          </div>
        </div>
        
        <div className="flex-1 flex flex-col gap-4 lg:gap-6 w-full px-2">
          <NavButton active={activeTab === 'monitor'} onClick={() => setActiveTab('monitor')} icon={<LayoutDashboard size={20} />} label="Monitor" />
          <NavButton active={activeTab === 'editor'} onClick={() => setActiveTab('editor')} icon={<FileText size={20} />} label="Flow" />
          <NavButton active={activeTab === 'manual'} onClick={() => setActiveTab('manual')} icon={<Gamepad2 size={20} />} label="Manual" />
        </div>

        <button className="mt-auto p-3 text-white/40 hover:text-white transition-colors">
           <Settings size={20} />
        </button>
      </nav>

      {/* 主内容 */}
      <main className="flex-1 flex flex-col relative bg-gradient-to-br from-neutral-950 to-black overflow-hidden">
        {/* 背景氛围 */}
        <div className="absolute top-[-10%] left-[20%] w-[40%] h-[40%] bg-blue-900/10 rounded-full blur-[120px] pointer-events-none mix-blend-screen" />
        <div className="absolute bottom-[-10%] right-[20%] w-[40%] h-[40%] bg-green-900/10 rounded-full blur-[120px] pointer-events-none mix-blend-screen" />

        {/* 顶部栏 */}
        <header className="h-14 lg:h-16 border-b border-white/5 flex items-center justify-between px-4 lg:px-6 bg-neutral-900/20 backdrop-blur-sm z-10 shrink-0">
          <div className="flex items-center gap-4">
             <h1 className="text-base lg:text-lg font-bold tracking-wide">TUBE LIFETIME TESTER <span className="text-blue-500">PRO</span></h1>
             <div className="h-4 w-[1px] bg-white/10" />
             
             {/* 连接状态按钮 */}
             <button 
                onClick={handleToggleConnection}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] lg:text-xs font-mono transition-all border ${
                 isConnected 
                   ? 'bg-green-500/10 text-green-400 border-green-500/20 hover:bg-green-500/20' 
                   : 'bg-red-500/10 text-red-400 border-red-500/20 hover:bg-red-500/20'
               }`}
             >
               {isConnected ? <Wifi size={12} /> : <WifiOff size={12} />}
               {isConnected ? 'ONLINE' : 'OFFLINE'}
             </button>

             {runState !== 'IDLE' && (
               <div className="flex items-center gap-2 text-xs font-mono text-white/50 ml-2">
                 <span className="flex h-2 w-2 relative">
                    <span className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${runState === 'RUNNING' ? 'animate-ping bg-green-400' : 'bg-yellow-400'}`}></span>
                    <span className={`relative inline-flex rounded-full h-2 w-2 ${runState === 'RUNNING' ? 'bg-green-500' : 'bg-yellow-500'}`}></span>
                 </span>
                 {runState}
               </div>
             )}
          </div>
 
          <div className="flex items-center gap-4 lg:gap-6">
             <div className="text-right flex flex-col items-end">
                <div className="text-[10px] text-white/40 font-bold tracking-wider mb-0.5">CYCLES</div>
                <div className="font-mono text-base lg:text-lg leading-none flex items-center gap-1">
                  <span className="text-white">{cycleCount.current}</span>
                  <span className="text-white/30 text-base"> / </span>
                  {/* 可编辑的循环次数 */}
                  {isEditingCycles ? (
                    <input 
                      autoFocus
                      type="number"
                      className="bg-neutral-800 text-white w-20 px-1 rounded border border-blue-500 outline-none text-base font-mono"
                      value={editTotalInput}
                      onChange={(e) => setEditTotalInput(e.target.value)}
                      onBlur={handleCycleSubmit}
                      onKeyDown={(e) => e.key === 'Enter' && handleCycleSubmit()}
                    />
                  ) : (
                    <span 
                      className="text-white/30 hover:text-white hover:underline cursor-pointer transition-colors flex items-center gap-1 group"
                      onClick={() => {
                         if(!isLocked) { // 运行时不可编辑
                             setEditTotalInput(cycleCount.total);
                             setIsEditingCycles(true);
                         }
                      }}
                      title="Click to edit total cycles"
                    >
                      {cycleCount.total}
                      {!isLocked && <Edit2 size={12} className="opacity-0 group-hover:opacity-50" />}
                    </span>
                  )}
                </div>
             </div>
             <div className="w-24 lg:w-32 h-1.5 bg-white/10 rounded-full overflow-hidden">
                <motion.div 
                  className="h-full bg-blue-500" 
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min((cycleCount.current / cycleCount.total) * 100, 100)}%` }}
                />
             </div>
          </div>
        </header>

        {/* 内容切换区 */}
        <div className="flex-1 p-4 lg:p-6 overflow-hidden relative flex flex-col">
          <AnimatePresence mode="wait">
            
            {/* --- PAGE 1: MONITOR --- */}
            {activeTab === 'monitor' && (
              <motion.div 
                key="monitor"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.3 }}
                className="grid grid-cols-12 gap-3 lg:gap-4 h-full min-h-0"
              >
                {/* 左侧：3D 可视化 (2/12) */}
                <div className="col-span-2 flex flex-col gap-3 h-full min-h-0">
                   <div className="flex-1 bg-neutral-900/40 border border-white/5 rounded-3xl relative overflow-hidden flex flex-col items-center justify-center gap-8 lg:gap-12 shadow-2xl backdrop-blur-sm min-h-0">
                      <Cylinder3D label="CYL-A" color={COLORS.primary} pos={cylA.pos} active={sequence[currentStepIdx]?.type === 'MOVE_A'} compact />
                      <Cylinder3D label="CYL-B" color={COLORS.secondary} pos={cylB.pos} active={sequence[currentStepIdx]?.type === 'MOVE_B'} compact />
                   </div>
                </div>

                {/* 中间：图表 (7/12) */}
                <div className="col-span-7 flex flex-col h-full min-h-0">
                   <div className="flex-1 bg-neutral-900/40 border border-white/5 rounded-3xl p-4 lg:p-5 flex flex-col backdrop-blur-sm shadow-xl relative overflow-hidden min-h-0">
                      <div className="flex items-center justify-between mb-2 lg:mb-4 z-10 shrink-0">
                         <div className="flex items-center gap-2 text-xs lg:text-sm font-bold text-white/70 uppercase tracking-widest">
                           <Activity size={16} className="text-blue-500"/> Real-time Force
                         </div>
                         <div className="flex gap-2 lg:gap-4 text-[9px] lg:text-[10px] font-bold bg-black/20 px-2 lg:px-3 py-1 rounded-full border border-white/5">
                            <span className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 lg:w-2 lg:h-2 rounded-full bg-blue-500"></span> CH-A</span>
                            <span className="flex items-center gap-1.5"><span className="w-1.5 h-1.5 lg:w-2 lg:h-2 rounded-full bg-green-500"></span> CH-B</span>
                         </div>
                      </div>
                      <div className="flex-1 relative w-full overflow-hidden min-h-0">
                         <RealTimeLineChart dataA={historyA} dataB={historyB} colorA={COLORS.primary} colorB={COLORS.secondary} />
                      </div>
                   </div>
                </div>

                {/* 右侧：数据与日志 (3/12) */}
                <div className="col-span-3 flex flex-col gap-3 h-full min-h-0">
                  <CompactStatusCard label="Cylinder A" pos={cylA.pos} force={cylA.force_out} color={COLORS.primary} />
                  <CompactStatusCard label="Cylinder B" pos={cylB.pos} force={cylB.force_out} color={COLORS.secondary} />

                   <div className="flex-1 bg-neutral-900/40 border border-white/5 rounded-3xl p-3 lg:p-4 flex flex-col overflow-hidden backdrop-blur-sm min-h-0">
                      <div className="flex items-center justify-between mb-2 shrink-0">
                        <div className="flex items-center gap-2 text-xs font-bold text-white/40 uppercase"><Terminal size={14} /> Log</div>
                        <button onClick={() => setLogs([])} className="text-[10px] text-white/20 hover:text-white transition"><Trash2 size={12}/></button>
                      </div>
                      <div className="flex-1 overflow-y-auto space-y-1.5 custom-scrollbar pr-1 font-mono text-[9px] lg:text-[10px]">
                         {logs.map((log, i) => (
                           <div key={i} className="flex gap-2 opacity-80 border-l-2 border-transparent hover:border-white/10 pl-1 transition-colors">
                             <span className="text-white/30 shrink-0">{new Date().toLocaleTimeString().split(' ')[0]}</span>
                             <span className={`truncate ${log.includes('STEP') ? 'text-blue-400' : log.includes('Error') ? 'text-red-400' : 'text-white/70'}`}>{log}</span>
                           </div>
                         ))}
                      </div>
                   </div>
                </div>
              </motion.div>
            )}

            {/* --- PAGE 2: EDITOR (流程编辑) --- */}
            {activeTab === 'editor' && (
              <motion.div 
                key="editor"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
                className="grid grid-cols-12 gap-4 lg:gap-6 h-full min-h-0"
              >
                {/* 流程列表 (8列) */}
                <div className="col-span-8 flex flex-col gap-4 h-full min-h-0">
                   {/* 改进 2: 文件名输入区域 */}
                   <div className="flex justify-between items-center px-2 shrink-0">
                      <div className="flex items-center gap-4">
                          <h2 className="text-lg lg:text-xl font-bold flex items-center gap-2"><FileText size={20} className="text-blue-500"/> Sequence Editor</h2>
                          <div className="h-6 w-[1px] bg-white/10" />
                          <div className={`flex items-center gap-2 bg-neutral-900/50 border border-white/5 px-3 py-1.5 rounded-lg transition-colors ${isLocked ? 'opacity-50' : 'focus-within:border-blue-500/50'}`}>
                             <FileType size={14} className="text-white/40"/>
                             <input 
                                disabled={isLocked}
                                type="text" 
                                value={fileName}
                                onChange={(e) => setFileName(e.target.value)}
                                className="bg-transparent border-none outline-none text-xs font-mono w-32 text-white placeholder-white/20"
                                placeholder="Sequence Name"
                             />
                             <span className="text-[10px] text-white/20">.json</span>
                          </div>
                      </div>
                      
                      {/* 改进 3: 编辑锁状态下禁用按钮 */}
                      <div className="flex gap-2">
                         <EditorToolButton disabled={isLocked} icon={<Save size={16}/>} label="Save" onClick={handleSave} />
                         <EditorToolButton disabled={isLocked} icon={<Upload size={16}/>} label="Load" onClick={handleLoad} />
                      </div>
                   </div>
                   
                   <div className="flex-1 bg-neutral-900/40 border border-white/5 rounded-3xl p-1 overflow-hidden backdrop-blur-sm min-h-0 relative">
                      {/* 改进 3: 锁屏遮罩 */}
                      {isLocked && (
                          <div className="absolute inset-0 z-10 bg-black/50 backdrop-blur-[1px] flex flex-col items-center justify-center text-white/30 gap-2 select-none">
                              <Lock size={32} />
                              <span className="text-xs font-bold uppercase tracking-widest">Locked while running</span>
                          </div>
                      )}
                      <div className="h-full overflow-y-auto custom-scrollbar p-3 lg:p-4">
                         <Reorder.Group axis="y" values={sequence} onReorder={isLocked ? () => {} : setSequence} className="space-y-2 lg:space-y-3">
                            {sequence.map((step) => (
                               <Reorder.Item key={step.id} value={step} dragListener={!isLocked}>
                                  <FlowStepCard 
                                    step={step} 
                                    disabled={isLocked}
                                    onDelete={() => setSequence(sequence.filter(s => s.id !== step.id))}
                                    onChange={(newVal) => setSequence(sequence.map(s => s.id === step.id ? {...s, ...newVal} : s))}
                                  />
                               </Reorder.Item>
                            ))}
                         </Reorder.Group>
                         {sequence.length === 0 && <div className="text-center text-white/20 py-10">No steps defined. Add one from the right.</div>}
                      </div>
                   </div>
                </div>

                {/* 工具箱 (4列) */}
                <div className={`col-span-4 flex flex-col gap-4 lg:gap-6 h-full min-h-0 transition-opacity duration-300 ${isLocked ? 'opacity-40 pointer-events-none' : ''}`}>
                   <div className="bg-neutral-900/40 border border-white/5 rounded-3xl p-4 lg:p-6 backdrop-blur-sm shrink-0">
                      <div className="text-xs font-bold text-white/40 uppercase mb-3 lg:mb-4">Add Step</div>
                      <div className="grid grid-cols-1 gap-2 lg:gap-3">
                         <AddStepButton 
                           label="Move Cylinder A" color="blue" 
                           onClick={() => setSequence([...sequence, { id: Date.now().toString(), type: 'MOVE_A', pos: 0, speed: 50, force: 100 }])} 
                         />
                         <AddStepButton 
                           label="Move Cylinder B" color="green" 
                           onClick={() => setSequence([...sequence, { id: Date.now().toString(), type: 'MOVE_B', pos: 0, speed: 50, force: 100 }])} 
                         />
                         <AddStepButton 
                           label="System Delay" color="orange" 
                           onClick={() => setSequence([...sequence, { id: Date.now().toString(), type: 'DELAY', time: 1 }])} 
                         />
                      </div>
                   </div>

                   <div className="bg-neutral-900/40 border border-white/5 rounded-3xl p-4 lg:p-6 backdrop-blur-sm flex-1 flex flex-col min-h-0">
                      <div className="text-xs font-bold text-white/40 uppercase mb-3 lg:mb-4">Validation</div>
                      <div className="flex-1 flex items-center justify-center text-center">
                         <div className="space-y-2">
                             <div className="w-10 h-10 lg:w-12 lg:h-12 rounded-full bg-green-500/20 text-green-500 flex items-center justify-center mx-auto mb-2"><Zap size={20} className="lg:w-6 lg:h-6"/></div>
                            <div className="text-xs lg:text-sm font-bold text-white/80">Valid Sequence</div>
                            <div className="text-[10px] lg:text-xs text-white/40">Ready to run</div>
                         </div>
                      </div>
                   </div>
                </div>
              </motion.div>
            )}

            {/* --- PAGE 3: MANUAL (手动模式) --- */}
            {activeTab === 'manual' && (
              <motion.div 
                key="manual"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
                className="grid grid-cols-2 gap-4 lg:gap-6 h-full min-h-0 overflow-auto"
              >
                 <ManualCard title="Cylinder A" color={COLORS.primary} pos={cylA.pos} />
                 <ManualCard title="Cylinder B" color={COLORS.secondary} pos={cylB.pos} />
              </motion.div>
            )}

          </AnimatePresence>
        </div>

        {/* 改进 1: 底部悬浮控制栏 (区分 Pause, Stop, Reset) */}
        {activeTab === 'monitor' && (
           <div className="absolute bottom-6 lg:bottom-8 left-1/2 -translate-x-1/2 flex gap-4 z-50">
            {runState === 'IDLE' ? (
                // 状态: IDLE - 显示 Start 和 Reset
                <div className="flex gap-4 items-center">
                    {/* RESET 按钮 (仅在 IDLE 时可见，或按需显示) */}
                    <motion.button 
                        whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                        onClick={handleReset}
                        className="h-10 px-4 bg-neutral-800 text-white/50 hover:text-white rounded-full font-bold text-xs flex items-center gap-2 border border-white/10"
                    >
                        <RefreshCw size={14} /> RESET
                    </motion.button>

                    <motion.button 
                        layoutId="fab"
                        whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                        onClick={handleStart}
                        className="h-12 lg:h-14 px-6 lg:px-8 bg-white text-black rounded-full font-bold text-base lg:text-lg flex items-center gap-2 shadow-[0_0_30px_-5px_rgba(255,255,255,0.4)]"
                    >
                        <Play fill="black" size={18} className="lg:w-5 lg:h-5" /> START TEST
                    </motion.button>
                </div>
            ) : (
              // 状态: RUNNING 或 PAUSED
              <motion.div layoutId="fab" className="flex gap-2 p-1.5 bg-neutral-900/90 backdrop-blur-md border border-white/10 rounded-full shadow-2xl">
                 {/* 暂停/继续 按钮 */}
                 {runState === 'RUNNING' ? (
                    <button onClick={handlePause} className="h-10 w-16 lg:h-12 lg:w-20 bg-yellow-600/20 text-yellow-500 border border-yellow-500/30 rounded-full flex items-center justify-center gap-1 hover:bg-yellow-600/30 transition">
                        <Pause fill="currentColor" size={16} className="lg:w-4 lg:h-4"/> 
                    </button>
                 ) : (
                    <button onClick={handleStart} className="h-10 w-16 lg:h-12 lg:w-20 bg-green-600/20 text-green-500 border border-green-500/30 rounded-full flex items-center justify-center gap-1 hover:bg-green-600/30 transition">
                        <Play fill="currentColor" size={16} className="lg:w-4 lg:h-4"/> 
                    </button>
                 )}
                 
                 {/* 停止 按钮 */}
                 <button onClick={handleStop} className="h-10 w-20 lg:h-12 lg:w-24 bg-red-500 rounded-full flex items-center justify-center gap-2 font-bold hover:bg-red-600 transition">
                    <Square fill="white" size={14} className="lg:w-4 lg:h-4"/> STOP
                 </button>
              </motion.div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

// --- 组件定义 ---

function NavButton({ active, onClick, icon, label }) {
  return (
    <button onClick={onClick} className="w-full aspect-square rounded-2xl flex flex-col items-center justify-center gap-1 relative z-10 group">
      {active && <motion.div layoutId="nav-bg" className="absolute inset-0 bg-white rounded-2xl shadow-lg shadow-white/10" transition={{ type: "spring", bounce: 0.2, duration: 0.6 }} />}
      <span className={`relative z-10 transition-colors ${active ? 'text-black' : 'text-white/40 group-hover:text-white/80'}`}>{icon}</span>
      <span className={`relative z-10 text-[9px] lg:text-[10px] font-bold transition-colors ${active ? 'text-black/70' : 'text-white/40 group-hover:text-white/80'}`}>{label}</span>
    </button>
  )
}

function FlowStepCard({ step, onDelete, onChange, disabled }) {
  const isDelay = step.type === 'DELAY';
  const color = isDelay ? COLORS.accent : (step.type.includes('A') ? COLORS.primary : COLORS.secondary);
  
  return (
    <motion.div 
      layout
      className={`bg-neutral-800/50 border border-white/5 rounded-xl p-2.5 lg:p-3 flex items-center gap-3 lg:gap-4 group transition-colors ${disabled ? 'opacity-80' : 'hover:border-white/10 cursor-grab active:cursor-grabbing'}`}
    >
      <div className="text-white/20"><MoveVertical size={16}/></div>
      <div className="w-7 h-7 lg:w-8 lg:h-8 rounded-lg flex items-center justify-center font-bold text-xs shadow-inner" 
           style={{ backgroundColor: `${color}20`, color: color }}>
        {isDelay ? <Clock size={14} className="lg:w-4 lg:h-4"/> : (step.type.includes('A') ? "A" : "B")}
      </div>
      <div className="flex-1 grid grid-cols-4 gap-2 lg:gap-4">
         <div className="flex flex-col justify-center">
            <span className="text-[9px] lg:text-[10px] font-bold text-white/30 uppercase">{step.type}</span>
         </div>
         {isDelay ? (
            <EditInput disabled={disabled} label="Time (s)" value={step.time} onChange={v => onChange({ time: parseFloat(v) })} />
         ) : (
           <>
             <EditInput disabled={disabled} label="Pos (mm)" value={step.pos} onChange={v => onChange({ pos: parseFloat(v) })} />
             <EditInput disabled={disabled} label="Speed (%)" value={step.speed} onChange={v => onChange({ speed: parseFloat(v) })} />
             <EditInput disabled={disabled} label="Force (%)" value={step.force} onChange={v => onChange({ force: parseFloat(v) })} />
           </>
         )}
      </div>
      <button disabled={disabled} onClick={onDelete} className={`p-2 text-white/20 rounded-lg transition-colors ${disabled ? 'cursor-not-allowed' : 'hover:text-red-500 hover:bg-red-500/10'}`}>
         <Trash2 size={14} className="lg:w-4 lg:h-4"/>
      </button>
    </motion.div>
  )
}

function EditInput({ label, value, onChange, disabled }) {
  return (
    <div className="flex flex-col gap-0.5 lg:gap-1">
       <label className="text-[8px] lg:text-[9px] text-white/30 font-bold uppercase">{label}</label>
       <input 
         disabled={disabled}
         type="number" 
         value={value} 
         onChange={(e) => onChange(e.target.value)}
         className={`bg-black/20 border border-white/10 rounded px-1.5 py-0.5 lg:px-2 lg:py-1 text-[10px] lg:text-xs font-mono text-white focus:outline-none transition-colors ${disabled ? 'text-white/50' : 'focus:border-blue-500'}`}
       />
    </div>
  )
}

function AddStepButton({ label, color, onClick }) {
  const bg = color === 'blue' ? 'bg-blue-600' : color === 'green' ? 'bg-green-600' : 'bg-orange-600';
  return (
    <button onClick={onClick} className={`w-full py-2.5 lg:py-3 ${bg} rounded-xl font-bold text-xs lg:text-sm flex items-center justify-center gap-2 hover:brightness-110 active:scale-98 transition-all`}>
       <Plus size={14} className="lg:w-4 lg:h-4"/> {label}
    </button>
  )
}

function EditorToolButton({ icon, label, onClick, disabled }) {
  return (
    <button disabled={disabled} onClick={onClick} className={`flex items-center gap-1.5 px-2.5 py-1.5 bg-white/5 border border-white/5 rounded-lg text-xs font-bold transition-colors ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-white/10'}`}>
       {icon} {label}
    </button>
  )
}

function ManualCard({ title, color, pos }) {
  return (
    <div className="bg-neutral-900/40 border border-white/5 rounded-3xl p-5 lg:p-8 flex flex-col relative overflow-hidden backdrop-blur-sm min-h-0">
       <div className="absolute top-0 right-0 p-24 lg:p-32 bg-gradient-to-br from-white/5 to-transparent rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none"/>
       <div className="flex items-center justify-between mb-6 lg:mb-8 z-10 shrink-0">
         <div className="flex items-center gap-3">
           <div className="w-3 h-3 rounded-full shadow-[0_0_10px]" style={{ backgroundColor: color, boxShadow: `0 0 15px ${color}` }} />
           <h3 className="text-lg lg:text-xl font-bold tracking-wide">{title}</h3>
         </div>
         <div className="font-mono text-xl lg:text-2xl font-bold">{pos?.toFixed(1)} <span className="text-sm text-white/40">mm</span></div>
       </div>
       <div className="grid grid-cols-2 gap-3 lg:gap-4 mb-4 lg:mb-6 z-10 shrink-0">
          <ManualBtn icon={<ChevronUp size={24}/>} label="JOG +" onHold={() => console.log('Jog +')} />
          <ManualBtn icon={<ChevronDown size={24}/>} label="JOG -" onHold={() => console.log('Jog -')} />
       </div>
       <div className="grid grid-cols-3 gap-2 lg:gap-3 z-10 shrink-0">
          <ManualActionBtn label="Step +" icon={<Plus size={14}/>} />
          <ManualActionBtn label="Step -" icon={<Move size={14}/>} />
          <ManualActionBtn label="Home" icon={<RotateCcw size={14}/>} highlight />
       </div>
       <div className="mt-auto pt-4 lg:pt-6 z-10 shrink-0">
          <div className="flex justify-between text-xs text-white/40 font-bold mb-2">
            <span>SPEED SETTING</span>
            <span>50%</span>
         </div>
          <input type="range" className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:rounded-full" />
       </div>
    </div>
  )
}

function ManualBtn({ icon, label, onHold }) {
  return (
    <button 
      onMouseDown={onHold} onMouseUp={() => console.log('Stop')} 
      className="h-20 lg:h-24 bg-white/5 border border-white/5 rounded-2xl flex flex-col items-center justify-center gap-2 hover:bg-white/10 active:bg-white/20 active:scale-95 transition-all"
    >
      {icon} <span className="text-xs font-bold tracking-wider opacity-60">{label}</span>
    </button>
  )
}

function ManualActionBtn({ label, icon, highlight }) {
  return (
    <button className={`h-10 lg:h-12 rounded-xl flex items-center justify-center gap-2 font-bold text-xs transition-all active:scale-95 ${highlight ? 'bg-white text-black hover:bg-gray-200' : 'bg-neutral-950 border border-white/10 text-white/60 hover:text-white hover:border-white/30'}`}>
       {icon} {label}
    </button>
  )
}

function Cylinder3D({ label, color, pos, active, compact }) {
  const height = useSpring(0, { stiffness: 60, damping: 15 });
  useEffect(() => {
    height.set(pos);
  }, [pos, height]);
  // Range 0-30mm mapped to 0-95%
  const hDisplay = useTransform(height, [0, 30], ["0%", "95%"]);
  return (
    <div className="flex flex-col items-center gap-2 lg:gap-3">
       <div className={`relative ${compact ? 'w-12 h-36 lg:w-14 lg:h-48' : 'w-14 h-40 lg:w-16 lg:h-56'} bg-neutral-900/50 rounded-full border border-white/10 flex items-end justify-center p-1.5 shadow-inner transition-all duration-300`}>
          <motion.div 
            className="w-full rounded-full relative z-10" 
            style={{ 
              height: hDisplay,
              backgroundColor: color, 
              boxShadow: `0 0 15px -2px ${color}50`
            }}
          >
             <div className="absolute top-1 left-1 right-1 h-1 bg-white/40 rounded-full" />
             {active && (
                <motion.div 
                 className="absolute inset-0 bg-white/30 rounded-full" 
                 animate={{ opacity: [0, 0.5, 0] }} 
                 transition={{ repeat: Infinity, duration: 1.2 }} 
               />
             )}
          </motion.div>
       </div>
       <div className="text-[9px] lg:text-[10px] font-bold text-white/40 tracking-widest">{label}</div>
    </div>
  )
}

function RealTimeLineChart({ dataA, dataB, colorA, colorB }) {
  const getPath = (data) => {
    if (!data.length) return "";
    const max = 150; 
    const width = 100; 
    const stepX = width / (data.length - 1);
    let d = `M 0 ${100 - (data[0] / max) * 100}`;
    for (let i = 1; i < data.length; i++) {
      const x = i * stepX;
      const y = 100 - (data[i] / max) * 100;
      d += ` L ${x} ${y}`;
    }
    return d;
  };

  return (
    <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
       <line x1="0" y1="25" x2="100" y2="25" stroke="white" strokeOpacity="0.05" strokeWidth="0.5" vectorEffect="non-scaling-stroke" />
       <line x1="0" y1="50" x2="100" y2="50" stroke="white" strokeOpacity="0.05" strokeWidth="0.5" vectorEffect="non-scaling-stroke" />
       <line x1="0" y1="75" x2="100" y2="75" stroke="white" strokeOpacity="0.05" strokeWidth="0.5" vectorEffect="non-scaling-stroke" />
       <path d={getPath(dataA)} fill="none" stroke={colorA} strokeWidth="2" vectorEffect="non-scaling-stroke" />
       <path d={getPath(dataB)} fill="none" stroke={colorB} strokeWidth="2" vectorEffect="non-scaling-stroke" strokeDasharray="4 2" />
    </svg>
  )
}

function CompactStatusCard({ label, pos, force, color }) {
  const circumference = 2 * Math.PI * 18;
  const offset = circumference - (force / 100) * circumference;
  return (
    <div className="bg-neutral-900/40 border border-white/5 rounded-2xl p-3 lg:p-4 flex items-center justify-between backdrop-blur-sm relative overflow-hidden group hover:bg-neutral-900/60 transition-colors shrink-0">
       <div className="absolute left-0 top-0 bottom-0 w-1" style={{ backgroundColor: color, opacity: 0.5 }} />
       <div className="flex items-center gap-2 lg:gap-3">
          <div className="relative w-10 h-10 lg:w-12 lg:h-12">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 50 50">
               <circle cx="25" cy="25" r="18" fill="none" stroke="white" strokeOpacity="0.1" strokeWidth="4" />
               <motion.circle 
                 cx="25" cy="25" r="18" fill="none" stroke={color} strokeWidth="4" strokeLinecap="round"
                 strokeDasharray={circumference}
                 animate={{ strokeDashoffset: offset }}
                 transition={{ type: "spring", stiffness: 60, damping: 20 }}
               />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
               <span className="text-[9px] lg:text-[10px] font-bold text-white/80">{force.toFixed(0)}</span>
            </div>
          </div>
          <div className="flex flex-col">
             <span className="text-[9px] lg:text-[10px] font-bold text-white/40 uppercase">{label}</span>
             <span className="text-[9px] lg:text-[10px] text-white/30">Output Load</span>
          </div>
       </div>
       <div className="text-right">
          <div className="text-[9px] lg:text-[10px] font-bold text-white/30 uppercase mb-0.5">POS (mm)</div>
          <div className="font-mono text-xl lg:text-2xl font-bold tracking-tighter" style={{ color: color }}>
             {pos?.toFixed(1)}
          </div>
       </div>
    </div>
  )
}