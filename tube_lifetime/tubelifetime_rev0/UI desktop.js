import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence, useSpring, useTransform } from 'framer-motion';
import { 
  Play, Pause, Square, 
  Settings, Activity, MoveVertical, 
  Zap, ChevronRight, BarChart3, 
  LayoutDashboard, FileText, Gamepad2, 
  Terminal, Gauge, AlertCircle
} from 'lucide-react';

// --- 配置与常量 ---
const COLORS = {
  bg: '#09090b', // Zinc 950
  panelBg: 'rgba(24, 24, 27, 0.6)', // Zinc 900/60
  primary: '#3b82f6', // Blue 500
  secondary: '#22c55e', // Green 500
  accent: '#f97316', // Orange 500
  danger: '#ef4444', // Red 500
  text: '#FFFFFF',
  border: 'rgba(255, 255, 255, 0.08)'
};

const INITIAL_SEQUENCE = [
  { id: 1, type: "MOVE_A", pos: 30.0, speed: 50.0, force: 100.0 },
  { id: 2, type: "DELAY", time: 1.0 },
  { id: 3, type: "MOVE_A", pos: 0.0, speed: 50.0, force: 100.0 },
  { id: 4, type: "MOVE_B", pos: 30.0, speed: 50.0, force: 100.0 },
  { id: 5, type: "DELAY", time: 1.0 },
  { id: 6, type: "MOVE_B", pos: 0.0, speed: 50.0, force: 100.0 },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('monitor'); 
  const [isRunning, setIsRunning] = useState(false);
  const [currentStepIdx, setCurrentStepIdx] = useState(-1);
  const [cycleCount, setCycleCount] = useState({ current: 0, total: 10000 });
  
  // 模拟电缸状态
  const [cylA, setCylA] = useState({ pos: 0, force: 0, target: 0 });
  const [cylB, setCylB] = useState({ pos: 0, force: 0, target: 0 });
  const [sequence, setSequence] = useState(INITIAL_SEQUENCE);
  const [logs, setLogs] = useState(["System initialized.", "Waiting for command..."]);

  // --- 模拟后台 Worker 逻辑 (仅用于前端演示) ---
  useEffect(() => {
    let interval;
    if (isRunning) {
      interval = setInterval(() => {
        // 模拟运动
        const updateCyl = (prev) => {
           const diff = prev.target - prev.pos;
           const step = diff * 0.15; 
           const newPos = Math.abs(diff) < 0.1 ? prev.target : prev.pos + step;
           const newForce = Math.abs(diff) > 1 ? (prev.force + (Math.random() * 15 - 5)) : 0;
           return { ...prev, pos: newPos, force: Math.max(0, Math.min(100, newForce)) };
        };
        setCylA(updateCyl);
        setCylB(updateCyl);

        // 模拟步进
        if (Math.random() > 0.96) {
          setCurrentStepIdx(prev => {
             const next = (prev + 1) % sequence.length;
             // 简单的日志模拟
             const step = sequence[next];
             setLogs(l => [`[STEP ${next+1}] ${step.type} Executing...`, ...l].slice(0, 8));
             return next;
          });
        }
      }, 50);
    }
    return () => clearInterval(interval);
  }, [isRunning, sequence]);

  // 监听步骤变化更新目标值
  useEffect(() => {
    if (currentStepIdx >= 0 && currentStepIdx < sequence.length) {
      const step = sequence[currentStepIdx];
      if (step.type === 'MOVE_A') setCylA(p => ({ ...p, target: step.pos }));
      if (step.type === 'MOVE_B') setCylB(p => ({ ...p, target: step.pos }));
      if (step.id === sequence.length && currentStepIdx === 0) {
         setCycleCount(c => ({...c, current: c.current + 1}));
      }
    }
  }, [currentStepIdx]);

  return (
    <div className="w-full h-screen bg-neutral-950 text-white font-sans flex overflow-hidden selection:bg-blue-500/30">
      
      {/* 左侧导航栏 (Sidebar) */}
      <nav className="w-20 border-r border-white/5 bg-neutral-900/50 flex flex-col items-center py-6 z-20 backdrop-blur-md">
        <div className="mb-8">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Activity className="text-white" size={20} />
          </div>
        </div>
        
        <div className="flex-1 flex flex-col gap-6 w-full px-3">
          <NavButton active={activeTab === 'monitor'} onClick={() => setActiveTab('monitor')} icon={<LayoutDashboard size={22} />} label="Monitor" />
          <NavButton active={activeTab === 'editor'} onClick={() => setActiveTab('editor')} icon={<FileText size={22} />} label="Flow" />
          <NavButton active={activeTab === 'manual'} onClick={() => setActiveTab('manual')} icon={<Gamepad2 size={22} />} label="Manual" />
        </div>

        <button className="mt-auto p-3 text-white/40 hover:text-white transition-colors">
          <Settings size={22} />
        </button>
      </nav>

      {/* 主内容区域 */}
      <main className="flex-1 flex flex-col relative">
        {/* 背景光效 */}
        <div className="absolute top-[-10%] left-[20%] w-[40%] h-[40%] bg-blue-900/10 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute bottom-[-10%] right-[20%] w-[40%] h-[40%] bg-green-900/10 rounded-full blur-[100px] pointer-events-none" />

        {/* 顶部状态栏 */}
        <header className="h-16 border-b border-white/5 flex items-center justify-between px-8 bg-neutral-900/20 backdrop-blur-sm z-10">
          <div className="flex items-center gap-4">
             <h1 className="text-lg font-bold tracking-wide">TUBE LIFETIME TESTER <span className="text-blue-500">PRO</span></h1>
             <div className="h-4 w-[1px] bg-white/10" />
             <div className="flex items-center gap-2 text-xs font-mono text-white/50">
               <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
               {isRunning ? 'SYSTEM RUNNING' : 'SYSTEM IDLE'}
             </div>
          </div>
          <div className="flex items-center gap-6">
             <div className="text-right">
                <div className="text-[10px] text-white/40 font-bold tracking-wider">CYCLE PROGRESS</div>
                <div className="font-mono text-lg leading-none">
                  <span className="text-white">{cycleCount.current}</span>
                  <span className="text-white/30"> / {cycleCount.total}</span>
                </div>
             </div>
             <div className="w-32 h-1.5 bg-white/10 rounded-full overflow-hidden">
                <motion.div 
                  className="h-full bg-blue-500" 
                  initial={{ width: 0 }}
                  animate={{ width: `${(cycleCount.current / cycleCount.total) * 100}%` }}
                />
             </div>
          </div>
        </header>

        {/* 核心工作区 (Grid Layout) */}
        <div className="flex-1 p-6 grid grid-cols-12 gap-6 overflow-hidden">
          
          {/* 左侧：可视化展示 (占 8 列) */}
          <div className="col-span-8 flex flex-col gap-6">
            
            {/* 3D 模拟窗口 */}
            <div className="flex-1 bg-neutral-900/40 border border-white/5 rounded-3xl relative overflow-hidden flex items-end justify-center pb-12 gap-20 shadow-2xl">
               {/* 网格背景 */}
               <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)', backgroundSize: '40px 40px', opacity: 0.5 }}></div>
               
               {/* 缸 A */}
               <Cylinder3D 
                 label="CYLINDER A" 
                 color={COLORS.primary} 
                 pos={cylA.pos} 
                 force={cylA.force}
                 active={sequence[currentStepIdx]?.type === 'MOVE_A'}
               />
               
               {/* 缸 B */}
               <Cylinder3D 
                 label="CYLINDER B" 
                 color={COLORS.secondary} 
                 pos={cylB.pos} 
                 force={cylB.force}
                 active={sequence[currentStepIdx]?.type === 'MOVE_B'}
               />
            </div>

            {/* 底部实时曲线/日志区 */}
            <div className="h-48 grid grid-cols-2 gap-6">
               {/* 简化的实时数据卡片 */}
               <div className="bg-neutral-900/40 border border-white/5 rounded-2xl p-4 flex flex-col justify-between">
                  <div className="flex items-center gap-2 text-xs font-bold text-white/40 uppercase">
                    <Gauge size={14} /> Real-time Sensors
                  </div>
                  <div className="grid grid-cols-2 gap-4 mt-2">
                    <SensorValue label="Force A" value={cylA.force} unit="%" color={COLORS.primary} />
                    <SensorValue label="Pos A" value={cylA.pos} unit="mm" color={COLORS.primary} />
                    <SensorValue label="Force B" value={cylB.force} unit="%" color={COLORS.secondary} />
                    <SensorValue label="Pos B" value={cylB.pos} unit="mm" color={COLORS.secondary} />
                  </div>
               </div>

               {/* 系统日志 */}
               <div className="bg-neutral-900/40 border border-white/5 rounded-2xl p-4 font-mono text-xs overflow-hidden flex flex-col">
                  <div className="flex items-center gap-2 text-xs font-bold text-white/40 uppercase mb-3">
                    <Terminal size={14} /> System Log
                  </div>
                  <div className="flex-1 overflow-y-auto space-y-1.5 opacity-80">
                    {logs.map((log, i) => (
                      <div key={i} className="flex gap-2">
                        <span className="text-white/30">{new Date().toLocaleTimeString().split(' ')[0]}</span>
                        <span className={log.includes('STEP') ? 'text-blue-400' : 'text-white/60'}>{log}</span>
                      </div>
                    ))}
                  </div>
               </div>
            </div>
          </div>

          {/* 右侧：控制面板 (占 4 列) */}
          <div className="col-span-4 flex flex-col gap-6">
            
            {/* 流程列表 */}
            <div className="flex-1 bg-neutral-900/40 border border-white/5 rounded-3xl p-5 flex flex-col overflow-hidden">
               <div className="flex justify-between items-center mb-4">
                 <span className="text-xs font-bold text-white/40 uppercase tracking-wider">Test Sequence</span>
                 <span className="text-xs bg-white/5 px-2 py-1 rounded text-white/40">{sequence.length} Steps</span>
               </div>
               
               <div className="flex-1 overflow-y-auto pr-1 space-y-2 no-scrollbar">
                  {sequence.map((step, idx) => (
                    <motion.div 
                      key={idx}
                      initial={false}
                      animate={{ 
                        backgroundColor: idx === currentStepIdx && isRunning ? 'rgba(59, 130, 246, 0.15)' : 'rgba(255,255,255,0.02)',
                        borderColor: idx === currentStepIdx && isRunning ? 'rgba(59, 130, 246, 0.4)' : 'transparent'
                      }}
                      className="border rounded-xl p-3 flex items-center gap-3 transition-colors"
                    >
                       <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold
                         ${step.type.includes('A') ? 'bg-blue-500/20 text-blue-400' : 
                           step.type.includes('B') ? 'bg-green-500/20 text-green-400' : 
                           'bg-orange-500/20 text-orange-400'}`}>
                         {idx + 1}
                       </div>
                       <div className="flex-1">
                         <div className="text-xs font-bold text-white/90">{step.type}</div>
                         <div className="text-[10px] text-white/40 mt-0.5">
                            {step.type === 'DELAY' ? `Wait ${step.time}s` : `Pos: ${step.pos}mm | F: ${step.force}%`}
                         </div>
                       </div>
                       {idx === currentStepIdx && isRunning && (
                         <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(59,130,246,0.8)]" />
                       )}
                    </motion.div>
                  ))}
               </div>
            </div>

            {/* 底部大控制区 */}
            <div className="h-auto bg-neutral-900/40 border border-white/5 rounded-3xl p-5">
               <div className="grid grid-cols-2 gap-3 h-24">
                 {!isRunning ? (
                   <button 
                    onClick={() => setIsRunning(true)}
                    className="col-span-2 bg-white hover:bg-white/90 text-black rounded-xl font-bold text-lg flex items-center justify-center gap-2 transition-transform active:scale-[0.98] shadow-lg shadow-white/10"
                   >
                     <Play size={20} fill="black" /> START TEST
                   </button>
                 ) : (
                   <>
                     <button 
                      onClick={() => setIsRunning(false)}
                      className="bg-neutral-800 hover:bg-neutral-700 text-white border border-white/10 rounded-xl font-bold flex items-center justify-center gap-2"
                     >
                       <Pause size={20} fill="white" /> PAUSE
                     </button>
                     <button 
                      onClick={() => {setIsRunning(false); setCurrentStepIdx(-1);}}
                      className="bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/20 rounded-xl font-bold flex items-center justify-center gap-2"
                     >
                       <Square size={18} fill="currentColor" /> STOP
                     </button>
                   </>
                 )}
               </div>
               
               <div className="flex items-center gap-2 mt-4 p-3 bg-blue-500/5 rounded-xl border border-blue-500/10">
                  <AlertCircle size={16} className="text-blue-400" />
                  <span className="text-xs text-blue-200/60">Safety guard active. Motors engaged.</span>
               </div>
            </div>

          </div>
        </div>
      </main>
    </div>
  );
}

// --- 组件定义 ---

function NavButton({ active, onClick, icon, label }) {
  return (
    <button 
      onClick={onClick}
      className={`w-full aspect-square rounded-2xl flex flex-col items-center justify-center gap-1 transition-all duration-300
        ${active ? 'bg-white text-black shadow-lg shadow-white/10' : 'text-white/40 hover:bg-white/5 hover:text-white/80'}
      `}
    >
      {icon}
      <span className="text-[10px] font-bold">{label}</span>
    </button>
  )
}

function Cylinder3D({ label, color, pos, force, active }) {
  const height = useSpring(pos, { stiffness: 60, damping: 15 });
  const hDisplay = useTransform(height, [0, 100], ["10%", "90%"]);
  
  return (
    <div className="relative w-32 h-[360px] flex flex-col items-center justify-end">
       {/* 标签 */}
       <div className="absolute -top-12 flex flex-col items-center">
          <div className="text-xs font-bold text-white/30 tracking-widest mb-1">{label}</div>
          <div className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-xs font-mono text-white/70 backdrop-blur-md">
             {pos.toFixed(1)} mm
          </div>
       </div>

       {/* 机械结构 */}
       <div className="w-24 h-full bg-neutral-800/80 rounded-t-2xl border-x border-t border-white/10 relative overflow-hidden backdrop-blur-sm shadow-2xl">
          {/* 刻度 */}
          <div className="absolute right-0 top-0 bottom-0 w-6 border-l border-white/5 flex flex-col justify-between py-4 items-end pr-1 opacity-30">
            {[...Array(10)].map((_,i) => <div key={i} className="w-3 h-[1px] bg-white"/>)}
          </div>

          {/* 活塞杆 */}
          <div className="absolute bottom-0 left-0 right-0 top-0 flex items-end justify-center pb-4">
             <motion.div 
               className="w-16 rounded-t-lg relative"
               style={{ 
                 height: hDisplay, 
                 backgroundColor: color,
                 boxShadow: `0 0 60px -10px ${color}60`
               }}
             >
                {/* 质感光泽 */}
                <div className="absolute top-0 inset-x-0 h-[1px] bg-white/60" />
                <div className="absolute top-2 left-2 w-3 h-20 bg-gradient-to-b from-white/30 to-transparent rounded-full blur-[1px]" />
                
                {/* 激活状态辉光 */}
                {active && (
                   <motion.div 
                     className="absolute inset-0 bg-white/20"
                     animate={{ opacity: [0, 0.4, 0] }}
                     transition={{ repeat: Infinity, duration: 1.5 }}
                   />
                )}
             </motion.div>
          </div>
       </div>

       {/* 底部受力指示灯 */}
       <div className="absolute bottom-0 w-36 h-2 rounded-full mt-4" style={{ backgroundColor: color, opacity: 0.2, filter: 'blur(10px)' }} />
    </div>
  )
}

function SensorValue({ label, value, unit, color }) {
  return (
    <div className="flex flex-col">
       <span className="text-[10px] text-white/30 font-bold uppercase">{label}</span>
       <div className="flex items-baseline gap-1">
         <span className="text-xl font-mono font-bold" style={{ color: color }}>
           {value.toFixed(1)}
         </span>
         <span className="text-xs text-white/40">{unit}</span>
       </div>
    </div>
  )
}