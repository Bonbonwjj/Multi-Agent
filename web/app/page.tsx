"use client";

import { useEffect, useState } from "react";

const phases = [
  { name:"需求分析", code:"DemandAnalysis", room:"design", roomName:"设计室", pair:"CEO × CPO", role:"CEO", color:"#f2b84b", output:"<INFO> Application", say:"先确认我们要做什么产品，以及怎样才算完成。", learn:"CEO 守住用户目标，CPO 将开放需求收敛成可实现的产品形态。" },
  { name:"语言选择", code:"LanguageChoose", room:"design", roomName:"设计室", pair:"CEO × CTO", role:"CTO", color:"#f28749", output:"<INFO> Python", say:"离线、零依赖，因此选择 Python 标准库。", learn:"同一个底层 LLM 因角色提示与上下文不同，形成不同的条件输出。" },
  { name:"初版编码", code:"Coding", room:"coding", roomName:"编码区", pair:"CTO × Programmer", role:"Programmer", color:"#6fa8dc", output:"task_app.py", say:"架构确认。现在生成完整文件，不留下 TODO。", learn:"CTO 给出架构约束；程序员把自然语言设计转换成可执行代码。" },
  { name:"代码补全", code:"CodeComplete × 10", room:"coding", roomName:"编码区", pair:"CTO × Programmer", role:"Programmer", color:"#7d8fe8", output:"完整代码", say:"检查缺失导入、文件、类和未实现方法。", learn:"最多十轮查漏补缺；连续无变化或返回 Finished 时终止。" },
  { name:"代码审查", code:"CodeReview × 3", room:"testing", roomName:"测试实验室", pair:"Programmer × Reviewer", role:"Reviewer", color:"#dc6b5f", output:"审查意见 → 修订", say:"这一轮只处理最高优先级缺陷。", learn:"审查者的目标函数是发现问题，能够打破生成者的自我确认偏差。" },
  { name:"系统测试", code:"SystemTest × 3", room:"testing", roomName:"测试实验室", pair:"Tester × Programmer", role:"Tester", color:"#59b98c", output:"Exit code: 0", say:"编译器反馈通过。运行状态已从错误转为成功。", learn:"真实执行结果是模型之外的证据，错误报告会进入下一轮上下文。" },
  { name:"环境文档", code:"EnvironmentDoc", room:"docs", roomName:"文档室", pair:"CTO × Programmer", role:"CTO", color:"#88b95b", output:"requirements.txt", say:"从最终代码反推依赖，不臆造包名。", learn:"依赖来自代码产物，而不是早期计划，因此与最终实现保持一致。" },
  { name:"用户手册", code:"Manual", room:"docs", roomName:"文档室", pair:"CEO × CPO", role:"CPO", color:"#d9a84e", output:"manual.md", say:"回到用户视角，写清安装、功能和用法。", learn:"最后阶段将技术产物重新翻译为用户能够理解的说明。" },
];

const roomPosition: Record<string, string> = { design:"hotspot design", coding:"hotspot coding", testing:"hotspot testing", docs:"hotspot docs" };

export default function Home() {
  const [active,setActive] = useState(0);
  const [running,setRunning] = useState(false);
  const [speed,setSpeed] = useState(1);
  const phase = phases[active];

  useEffect(() => {
    if (!running) return;
    const timer = window.setTimeout(() => {
      if (active >= phases.length - 1) setRunning(false); else setActive(active + 1);
    }, 1250 / speed);
    return () => window.clearTimeout(timer);
  }, [running, active, speed]);

  function start() { setActive(0); setRunning(true); }

  return <main className="gameShell">
    <header className="gameHeader">
      <div className="pixelLogo"><span>CD</span><div><b>CHATDEV</b><small>VIRTUAL SOFTWARE COMPANY</small></div></div>
      <div className="projectTitle"><small>CURRENT MISSION</small><b>开发一个离线待办事项工具</b></div>
      <div className="headerStats"><span><i className="greenDot"/> SYSTEM ONLINE</span><span>ACL · 2024</span><a href="https://github.com/OpenBMB/ChatDev/tree/chatdev1.0" target="_blank">SOURCE ↗</a></div>
    </header>

    <section className="gameLayout">
      <aside className="leftPanel pixelPanel">
        <div className="panelTitle"><span>◈</span><div><b>CHAT CHAIN</b><small>8 PHASES</small></div></div>
        <div className="phaseList">
          {phases.map((p,i)=><button key={p.code} className={`${active===i?"active":""} ${i<active?"complete":""}`} onClick={()=>{setRunning(false);setActive(i)}}>
            <i style={{background:p.color}}>{i<active?"✓":String(i+1).padStart(2,"0")}</i><span><b>{p.name}</b><small>{p.code}</small></span><em>{active===i?"▶":""}</em>
          </button>)}
        </div>
        <div className="memoryMeter"><div><span>CONTEXT MEMORY</span><b>42%</b></div><progress value="42" max="100"/><small>只传递阶段结论，过滤无关对话</small></div>
      </aside>

      <section className="officePanel pixelPanel">
        <div className="officeToolbar"><span>◉ LIVE OFFICE</span><span>{phase.roomName} · {phase.pair}</span><span className={running?"live":""}>{running?"● RUNNING":"Ⅱ PAUSED"}</span></div>
        <div className="officeScene">
          <img src="/pixel-office.png" alt="ChatDev 像素风虚拟软件公司，包含设计、编码、测试和文档区域"/>
          {Object.entries(roomPosition).map(([room,cls])=><button key={room} aria-label={`进入${room}`} className={`${cls} ${phase.room===room?"selected":""}`} onClick={()=>{const i=phases.findIndex(p=>p.room===room);setActive(i);setRunning(false)}}><span>{phases.find(p=>p.room===room)?.roomName}</span></button>)}
          <div className={`speech ${phase.room}`}><b>{phase.role}</b><p>{phase.say}</p><span/></div>
          <div className="scanline"/>
        </div>
        <div className="playbar">
          <button className="play" onClick={()=>running?setRunning(false):start()}>{running?"Ⅱ":"▶"}</button>
          <div className="timeline">{phases.map((p,i)=><button key={p.code} aria-label={p.name} className={i===active?"now":i<active?"past":""} onClick={()=>{setActive(i);setRunning(false)}}><span/></button>)}</div>
          <label>速度 <input type="range" min="1" max="3" step="1" value={speed} onChange={e=>setSpeed(Number(e.target.value))}/><b>{speed}×</b></label>
        </div>
      </section>

      <aside className="rightPanel pixelPanel">
        <div className="panelTitle"><span>▤</span><div><b>SEMINAR LOG</b><small>ROUND {String(active+1).padStart(2,"0")}</small></div></div>
        <div className="roleCards"><div><span className="pixelFace instructor">I</span><p><small>INSTRUCTOR</small><b>{phase.pair.split(" × ")[0]}</b></p></div><i>⇄</i><div><span className="pixelFace assistant">A</span><p><small>ASSISTANT</small><b>{phase.pair.split(" × ")[1]}</b></p></div></div>
        <div className="log"><div><span>INSTRUCTION</span><p>完成 {phase.name}，遵循输出契约。</p></div><div className="clarify"><span>CLARIFY · CDH</span><p>在正式回答前，先暴露一个关键不确定性。</p></div><div className="solution"><span>SOLUTION</span><code>{phase.output}</code></div></div>
        <div className="knowledge"><span>本阶段知识点</span><p>{phase.learn}</p><code>P(y | S_role, M, x)</code></div>
        <div className="artifact"><span>NEW ARTIFACT</span><div><i>◆</i><p><b>{phase.output}</b><small>已写入长期记忆</small></p><em>+1</em></div></div>
      </aside>
    </section>

    <footer className="statusBar"><span>◫ FILES <b>{Math.min(active+1,4)}</b></span><span>↻ VERSION <b>{active+1}</b></span><span>✓ TESTS <b>{active>=5?"PASS":"WAIT"}</b></span><p>提示：点击办公室房间或左侧阶段可以自由探索算法</p><span className="clock">CHATDEV LAB · PAPER REPRODUCTION</span></footer>
  </main>
}
