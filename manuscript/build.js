const fs = require("fs");
const d = require("docx");
const {
  Document, Packer, Paragraph, TextRun, AlignmentType, HeadingLevel,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, ImageRun,
  PageOrientation, SectionType, convertInchesToTwip,
} = d;

// ---- palette / type, matched to the reference manuscript -----------------
const NAVY = "1F4E79";
const MID = "2E74B5";
const BAND = "DEEBF7";
const SERIF = "Times New Roman";
const BODY = 20;   // 10pt, half-points
const SMALL = 17;

const NONE = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: NONE, bottom: NONE, left: NONE, right: NONE };

// ---- helpers -------------------------------------------------------------
const p = (text, o = {}) =>
  new Paragraph({
    alignment: o.align || AlignmentType.JUSTIFIED,
    spacing: { after: o.after === undefined ? 120 : o.after, line: 240 },
    indent: o.indent,
    children: [new TextRun({ text, font: SERIF, size: o.size || BODY,
      bold: o.bold, italics: o.italics, color: o.color })],
  });

// paragraph built from [text, {bold/italics}] fragments
const rich = (parts, o = {}) =>
  new Paragraph({
    alignment: o.align || AlignmentType.JUSTIFIED,
    spacing: { after: o.after === undefined ? 120 : o.after, line: 240 },
    children: parts.map(([t, f = {}]) =>
      new TextRun({ text: t, font: SERIF, size: o.size || BODY, ...f })),
  });

// SECTION HEADING — light band, navy caps, thick left rule
const h1 = (text) =>
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 260, after: 140 },
    shading: { type: ShadingType.CLEAR, fill: BAND, color: "auto" },
    border: { left: { style: BorderStyle.SINGLE, size: 18, color: NAVY, space: 6 } },
    indent: { left: 90 },
    children: [new TextRun({ text: text.toUpperCase(), font: SERIF, size: 22,
      bold: true, color: NAVY })],
  });

const h2 = (text) =>
  new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text, font: SERIF, size: BODY, bold: true, color: MID })],
  });

// centred, italic equation with a right-aligned number
const eq = (body, n) =>
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 140, after: 140 },
    children: [
      new TextRun({ text: body, font: SERIF, size: BODY, italics: true }),
      new TextRun({ text: "  ", font: SERIF, size: BODY }),
      new TextRun({ text: `(${n})`, font: SERIF, size: BODY }),
    ],
  });

const caption = (text) =>
  new Paragraph({
    spacing: { before: 160, after: 80 },
    children: [new TextRun({ text, font: SERIF, size: SMALL, bold: true, color: NAVY })],
  });

const cell = (text, { header = false, w, bold = false, align } = {}) =>
  new TableCell({
    width: { size: w, type: WidthType.DXA },
    shading: header
      ? { type: ShadingType.CLEAR, fill: NAVY, color: "auto" }
      : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [
      new Paragraph({
        alignment: align || AlignmentType.LEFT,
        spacing: { after: 0, line: 220 },
        children: [new TextRun({
          text, font: SERIF, size: SMALL,
          bold: header || bold,
          color: header ? "FFFFFF" : undefined,
        })],
      }),
    ],
  });

const table = (widths, rows) =>
  new Table({
    columnWidths: widths,
    width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    rows: rows.map((cells, i) =>
      new TableRow({
        tableHeader: i === 0,
        children: cells.map((t, j) => cell(t, { header: i === 0, w: widths[j] })),
      })),
  });

// section property blocks
const ONE_COL = { type: SectionType.CONTINUOUS };
const TWO_COL = { type: SectionType.CONTINUOUS, column: { count: 2, space: 380, equalWidth: true } };
const PAGE = {
  page: {
    size: { width: 12240, height: 15840 },
    margin: { top: 1100, right: 1100, bottom: 1100, left: 1100 },
  },
};
const sec = (props, children) => ({ properties: { ...PAGE, ...props }, children });

// =========================================================================
// FRONT MATTER  (single column)
// =========================================================================
const front = [
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
    children: [new TextRun({
      text: "RUNTIME TEAM FORMATION IN A CLOUD-NATIVE MULTI-AGENT SYSTEM BUILT ON OPEN AGENT STANDARDS",
      font: SERIF, size: 30, bold: true, color: NAVY })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 220 },
    border: { top: { style: BorderStyle.SINGLE, size: 8, color: NAVY, space: 6 },
              bottom: { style: BorderStyle.SINGLE, size: 8, color: NAVY, space: 6 } },
    children: [new TextRun({ text: "[Author name and affiliation]", font: SERIF, size: BODY, italics: true })],
  }),
  h1("Abstract"),
  new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 160, line: 240 },
    shading: { type: ShadingType.CLEAR, fill: "F2F7FC", color: "auto" },
    border: {
      top: { style: BorderStyle.SINGLE, size: 4, color: "BDD7EE", space: 8 },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: "BDD7EE", space: 8 },
      left: { style: BorderStyle.SINGLE, size: 4, color: "BDD7EE", space: 8 },
      right: { style: BorderStyle.SINGLE, size: 4, color: "BDD7EE", space: 8 },
    },
    children: [new TextRun({ font: SERIF, size: BODY, text:
      "Agentic applications increasingly decompose a task across several specialised agents, but the composition of those agents is almost always fixed when the system is written. Cloud-native deployment makes that assumption unsound: agents are independently deployed services that scale, fail and appear while the system is running, so a team enumerated in source contradicts the environment it runs in. This chapter presents an agentic document-research system in which four specialised agents communicate through the Agent2Agent protocol, reach their tools through the Model Context Protocol, and run as independent workloads on Kubernetes; and it replaces the hardcoded team with formation performed at run time. Agents advertise consumed and produced information types in their A2A capability cards, and a coordinator derives both the membership and the ordering of a team by chaining those declarations. Formation was evaluated across four conditions, four deployment scenarios and fourteen tasks, giving 224 trials; because formation performs no model inference, the measurements are exact rather than sampled, and per-task ground truth was fixed before any result was observed. The first mechanism proved less precise than the static team it replaced, scoring 0.705 against 0.786, because formation never observed the task and therefore recruited every runnable agent irrespective of need. Introducing requirement markers, by which a task is profiled for the needs it raises and an agent earns inclusion only by necessity or by satisfying a marker, raised precision to 1.000 with perfect recall and reduced the mean team from 3.50 to 2.36 agents, with no source modification across any scenario. The clearest evidence for the mechanism is a reduction in completions: when the analysis agent is withdrawn, task-blind formation answers arithmetic questions using a team containing no arithmetic agent and reports success, whereas task-aware formation reports those tasks as impossible and names the absent capability." })],
  }),
  rich([["Categories: ", { bold: true, color: NAVY }],
        ["Multi-Agent Systems, Distributed Systems, Cloud-Native Computing, Software Architecture, Agentic Artificial Intelligence"]],
       { after: 60, size: SMALL }),
  rich([["Keywords: ", { bold: true, color: NAVY }],
        ["agentic systems, multi-agent systems, Model Context Protocol, Agent2Agent protocol, Kubernetes, capability-based discovery, team formation, service discovery, interoperability"]],
       { after: 200, size: SMALL }),
];

// =========================================================================
// BODY PART 1 — Introduction + Related Works prose (two columns)
// =========================================================================
const body1 = [
  h1("Introduction"),
  p("An agentic application is one in which a language model is permitted to act: to select a tool, observe its result, and decide what to do next. Where a task is large or heterogeneous, such applications are commonly decomposed across several agents, each given a narrower brief, on the reasoning that specialisation improves the quality of each part and that the parts compose."),
  p("The decomposition is ordinarily fixed by the author. A coordinator is written knowing which agents exist, what each is for, and the order in which they should be consulted. This is a reasonable arrangement when the agents are objects in a single process, because in that setting the author's knowledge is complete and remains correct for the lifetime of the program."),
  p("Cloud-native deployment removes that guarantee. When each agent is an independently deployed service, the population of agents is a property of the cluster rather than of the source: replicas scale with load, pods are rescheduled onto different nodes, an agent may be withdrawn for maintenance, and a new agent may be deployed by someone who has never read the coordinator. A team enumerated in source therefore asserts, at authoring time, three facts that are not knowable at authoring time — which agents exist, how many there are, and where they are — and the assertion silently decays as the deployment changes."),
  p("This chapter treats that contradiction as the problem to be solved. It first constructs the system the contradiction arises in: an agentic document-research application whose agents communicate over an open agent-to-agent protocol, reach their tools over an open agent-to-tool protocol, and run as independent Kubernetes workloads. It then replaces the enumerated team with a mechanism that derives the team at run time from capabilities the agents themselves advertise."),
  p("Three contributions follow. The first is a capability declaration carried inside standard A2A card tags, by which an agent states the information types it consumes and produces, so that a chain of agents can be derived rather than written. The second is a formation procedure over those declarations, including an ordering rule that distinguishes agents which refine an information type from those which transform it. The third is a controlled evaluation of formation against the static arrangement it replaces, which produced a negative intermediate result that is retained and analysed here, since it motivated the final mechanism."),

  h1("Related Works"),
  p("Cloud-native execution of multi-agent systems predates the current generation of language-model agents. Work on scalable and fault-tolerant multi-agent platforms established that container orchestration supplies the scheduling, restart and discovery primitives such systems require, and demonstrated a cloud-native agent platform on that basis [ref]. That work concerns agent platforms in the classical sense, in which agent behaviour is programmed rather than elicited from a model, and the question of how a coordinator learns what its peers can do does not arise, because the platform defines it."),
  p("Interoperability between model-driven agents has since been addressed by open protocols. The Model Context Protocol standardises the vertical interface between an agent and the tools or data it uses, and the Agent2Agent protocol standardises the horizontal interface between agents, permitting delegation between peers built on different frameworks [ref]. Comparative analyses of these protocols and of adjacent proposals describe them as complementary layers of a single interoperability stack and examine how they combine in practice [ref], [ref]. This literature establishes the interfaces used in the present work but is concerned with the protocols themselves rather than with what a system should do with the information they expose."),
  p("Protocol performance has been benchmarked directly. ProtocolBench compares agent interoperability protocols on task success, end-to-end latency, message overhead and robustness under induced failure, and reports material differences between them [ref]. That evaluation takes the protocol as the object of study and holds the agent arrangement constant; the present work inverts this, holding the protocol constant and varying how the arrangement is decided."),
  p("The value of multi-agent decomposition is itself contested. A taxonomy of multi-agent failures derived from a large corpus of execution traces identifies fourteen distinct failure modes across three categories, and reports that performance gains from decomposition on common benchmarks are frequently marginal [ref]. A more pointed result shows that when the reasoning-token budget is held constant, single-agent systems match or exceed multi-agent systems on multi-hop reasoning, implying that reported gains often reflect additional computation rather than architecture [ref]. Industrial practice has made a related argument on the grounds of context fragmentation between agents [ref]. These findings bear directly on the measures adopted here: a mechanism that recruits agents without need is not merely inefficient but may be actively harmful, which is why precision against a fixed notion of necessity is treated as a first-class measure rather than as a proxy for cost."),
  p("Infrastructure for deploying model-driven agents on Kubernetes is developing rapidly. Open-source frameworks for running agents as cluster workloads exist, sandbox and substrate custom resources are under development, and a foundation-level initiative is drafting an agent custom resource definition together with lifecycle states, cluster-level discovery and protocol-aware gateways [ref], [ref]. A gap analysis of agentic web infrastructure catalogues missing capabilities across a layered reference architecture and identifies the transition from keyword-based to semantic, trust-weighted agent discovery as an unaddressed evolution path [ref]. The present work does not contribute to this infrastructure layer, and deliberately claims no novelty in it; it consumes the label-based service discovery Kubernetes already provides, and asks instead what a coordinator should do with the set of agents that discovery returns."),
  p("Three gaps follow. First, agent topology in reported multi-agent systems is overwhelmingly static and author-defined, so the composition of the team is not a variable and has not been evaluated as one. Second, where discovery is discussed it is treated as an infrastructure concern, and the step from a discovered set of agents to a working team is left unspecified. Third, the literature that questions the value of decomposition measures outcome quality but not team composition, so the cost of recruiting an unnecessary agent is not separately quantified. This chapter addresses all three."),
];

// Table 1 — full width, single column
const table1 = [
  caption("Table 1. Summary of reviewed studies."),
  table([2050, 2750, 2200, 2900], [
    ["Work", "Contribution", "Agent topology", "Limitation for this problem"],
    ["Cloud-native MAS platform [ref]", "Scalable, fault-tolerant agent platform on cloud-native primitives", "Platform-defined", "Pre-dates model-driven agents; peer capability is defined by the platform, not advertised"],
    ["MCP and A2A specifications [ref]", "Open agent-to-tool and agent-to-agent interfaces", "Not addressed", "Defines how agents communicate, not how a team is composed"],
    ["Interoperability protocol surveys [ref], [ref]", "Comparative analysis of MCP, ACP, A2A, ANP", "Not addressed", "Descriptive; no mechanism proposed over the advertised information"],
    ["ProtocolBench [ref]", "Benchmarks protocols on success, latency, overhead, failure robustness", "Held constant", "Protocol is the variable; arrangement of agents is fixed"],
    ["Multi-agent failure taxonomy [ref]", "14 failure modes over 3 categories from trace analysis", "Static", "Measures outcome quality, not team composition"],
    ["Equal-budget single vs multi-agent [ref]", "Single agents match or beat multi-agent under fixed token budget", "Static", "Implies unnecessary agents are harmful, but does not measure recruitment"],
    ["Kubernetes-native agent infrastructure [ref], [ref]", "Agent workloads, sandbox and substrate resources, draft agent CRD", "Deployment-level", "Supplies discovery; does not specify use of its result"],
    ["Agentic web gap analysis [ref]", "Layered reference architecture and capability gap taxonomy", "Not addressed", "Identifies semantic discovery as unbuilt; proposes no mechanism"],
    ["This work", "Capability-declared, task-aware runtime team formation", "Derived per run", "—"],
  ]),
];

// =========================================================================
// METHODS (two columns)
// =========================================================================
const body2a = [
  h1("Materials and Methods"),

  h2("System architecture"),
  p("The application answers a natural-language question against a local document corpus and returns a cited report. Four agents participate. A research agent retrieves passages relevant to a query and reports what they contain. A fact-checking agent re-examines supplied claims against the corpus and annotates each as confirmed, contradicted or absent. An analysis agent reasons and computes over supplied material. A writer agent composes the final answer from what it is given and introduces no new claims."),
  p("Each agent is an autonomous loop: a request is sent to a model together with the agent's tool schemas; if the response contains tool calls they are executed and their results returned; the loop terminates when the model requests no further tools. The agents differ only in their brief and their permitted tools, so the loop is implemented once and shared."),
  p("All tool access passes through the Model Context Protocol. No agent imports a tool function directly; an MCP server exposes corpus search and arithmetic, and each agent discovers the available tools from that server at start-up. All inter-agent communication passes through the Agent2Agent protocol, each agent publishing a capability card at a well-known endpoint and accepting tasks over JSON-RPC. Each agent is packaged as a container and deployed as a Kubernetes Deployment with an associated Service, an HTTP readiness probe that retrieves the agent's own capability card, and an independently adjustable replica count."),

];

const body2b = [
  h2("Capability declaration"),
  p("An agent advertises its role in machine-readable form through tags carried in its A2A capability card. Let an agent be characterised as in Equation (1), where C denotes the information types the agent requires, P the types it returns, and S the requirement markers it is able to satisfy."),
  eq("a = ( Cₐ , Pₐ , Sₐ )", 1),
  p("These tags are ordinary A2A card tags. A client that does not implement the convention ignores them without error, so an agent carrying them remains a conformant A2A peer. Given a set A of information types already available, an agent is eligible to run when its requirements are satisfied, as in Equation (2)."),
  eq("run( a , A )  ⇔  Cₐ ⊆ A", 2),

  h2("Formation by chaining"),
  p("A team is a sequence of agents beginning from a raw query and terminating when a report has been produced. Formation proceeds by forward chaining: an eligible agent is selected, its outputs are added to the available set, and selection repeats until the goal type is available or no eligible agent remains. When no chain reaches the goal, the outcome is reported together with the types that could be produced, rather than raised as a failure."),
  p("Selection among several eligible agents determines whether the resulting order is merely valid or also sensible. The distinction that governs it is given in Equation (3): an agent that returns a type it consumed refines that type and leaves it available to subsequent agents, whereas an agent that consumes a type and returns only different types transforms it, ending that type's availability in the chain."),
  eq("refiner( a )  ⇔  Cₐ ∩ Pₐ ≠ ∅", 3),
  p("A refiner of a given type must therefore precede any transformer of that type, since after the transformation the refined material is no longer read. Selection accordingly prefers refiners, breaking remaining ties by agent name so that a given deployment always yields the same plan. No per-type bookkeeping is required, because a refiner of a downstream type cannot become eligible until that type exists, which occurs only after the agents producing it have run."),

  h2("Task-aware formation"),
  p("Chaining as described consults only the declared capabilities of the deployed agents. It never observes the task, and therefore derives an identical team for a question requiring arithmetic and one requiring none. To address this, a task is profiled into the set R of requirement markers it raises, and an agent earns inclusion only by being necessary to reach the goal or by satisfying a marker in R. Formation then searches for the smallest agent set satisfying Equation (4), and orders that set by the rule already established."),
  eq("T* = arg min |T|  s.t.  goal ∈ A(T)  ∧  R ⊆ ∪ₐ₊ₜ Sₐ", 4),
  p("The search is breadth-first, so the first satisfying set encountered is of minimum size, and candidates are expanded in name order so that the result is reproducible. Where no set both reaches the goal and covers R, the task is reported as impossible and the uncovered markers are named. Returning a goal-reaching chain in that circumstance would be worse than returning nothing, since it would answer a question requiring computation with a team containing no agent able to compute, and would report success in doing so."),
  p("The profiler used here is a keyword matcher over the task text. This is a deliberate choice rather than a convenience: it keeps formation free of model inference, and therefore exactly measurable rather than sampled. Its generality is examined in the Discussion."),

  h2("Experimental design"),
  p("Four conditions were compared. The static condition is the arrangement the system had before formation was introduced, in which the team is written in source and is insensitive to what is deployed. The first derived condition is formation as originally implemented, blind to the task. The second derived condition isolates a change made to one agent's declaration, without task-awareness, so that its effect is not confounded with the mechanism. The targeted condition is task-aware formation as described above."),
  p("Four deployment scenarios were used: a baseline of three agents; a fourth agent deployed after the system was written; withdrawal of a middle agent in the chain; and withdrawal of the entry agent. Fourteen tasks were used: three requiring a single retrieved fact, two requiring synthesis across documents, five requiring arithmetic the corpus does not state, two presenting a claim to be checked against the corpus, and two whose answers are absent from the corpus altogether. The full design is therefore four conditions by four scenarios by fourteen tasks, giving 224 trials."),
  p("For each task, the minimal set of agents genuinely required to answer it was recorded in advance of any result being observed. Precision and recall of the formed team were computed against that set as in Equations (5) and (6), where T is the team formed and N the required set. Precision penalises the recruitment of agents outside the required set; recall penalises omission of a required agent."),
  eq("Precision = | T ∩ N | / | T |", 5),
  eq("Recall = | T ∩ N | / | N |", 6),
  p("Three further measures were recorded: the number of source modifications required to accommodate each scenario; the mean size of the formed team; and the manner of failure, distinguishing a task reported as impossible before any agent is invoked from one discovered to be impossible by invoking an agent that is not deployed."),
  p("Because formation performs no model inference, every measurement is deterministic. No repetition or averaging over runs is required, and reported figures carry no sampling error. End-to-end answers were additionally generated using a locally hosted seven-billion-parameter model, confirming that the derived teams execute and produce cited answers, but answer quality is not among the measures reported here."),
];


// ---- figures ---------------------------------------------------------
const figure = (file, w, h, capText) => [
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 80 },
    children: [new ImageRun({ type: "png", data: fs.readFileSync(file),
      transformation: { width: w, height: h } })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 180 },
    children: [new TextRun({ text: capText, font: SERIF, size: SMALL, bold: true, color: NAVY })],
  }),
];

const figureArch = figure("figure_architecture.png", 668, 413,
  "Figure 1. System architecture. Agents are independently deployed workloads; A2A carries agent-to-agent traffic and MCP carries all tool access. The coordinator learns which agents exist by querying the cluster, not from its own source.");

const figureWithdraw = figure("figure_withdrawal.png", 668, 340,
  "Figure 3. Withdrawal of an agent during execution, under a fixed plan and under re-formation. Recovery is possible only where a second agent satisfies the same requirement.");

// ---- Figure 2 ------------------------------------------------------------
const figure1 = [
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 80 },
    children: [new ImageRun({
      type: "png",
      data: fs.readFileSync("figure_formation.png"),
      transformation: { width: 668, height: 391 },
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 180 },
    children: [new TextRun({
      text: "Figure 2. The same deployment yielding different teams for two tasks. Membership is decided by the requirements the task raises, not by which agents happen to be eligible.",
      font: SERIF, size: SMALL, bold: true, color: NAVY })],
  }),
];

const table2 = [
  caption("Table 2. Experimental configuration."),
  table([2400, 3100, 2200, 2200], [
    ["Parameter", "Value", "Parameter", "Value"],
    ["Conditions", "4 (static, derived, derived+loosened, targeted)", "Tasks", "14"],
    ["Deployment scenarios", "4", "Trials", "224"],
    ["Agents available", "4 (research, factcheck, analysis, writer)", "Inference in formation", "None"],
    ["Agent-to-tool interface", "Model Context Protocol", "Repetitions", "1 (deterministic)"],
    ["Agent-to-agent interface", "Agent2Agent protocol", "Ground truth", "Fixed before observation"],
    ["Orchestration", "Kubernetes (k3s)", "Goal type", "report"],
  ]),
];

// =========================================================================
// RESULTS
// =========================================================================
const body3 = [
  h1("Results"),
  p("Table 3 reports the headline comparison. The static team and task-blind formation are separated by no single measure that favours formation unambiguously; the static team is in fact the more precise of the two. Task-aware formation dominates both."),
];

const table3 = [
  caption("Table 3. Formation quality by condition, over 224 trials. Precision and recall are means over completing trials."),
  table([2980, 1384, 1384, 1384, 1384, 1384], [
    ["Condition", "Precision", "Recall", "Team size", "Source edits", "Runtime failures"],
    ["Static team", "0.786", "0.952", "3.00", "42", "28"],
    ["Derived, as first implemented", "0.705", "0.976", "3.50", "0", "0"],
    ["Derived, loosened declaration only", "0.804", "0.929", "3.00", "0", "0"],
    ["Targeted (task-aware)", "1.000", "1.000", "2.36", "0", "0"],
  ]),
  caption("Table 4. Tasks completed out of fourteen, by deployment scenario."),
  table([2900, 1750, 1750, 1750, 1750], [
    ["Scenario", "Static", "Derived", "Derived, loosened", "Targeted"],
    ["Baseline (three agents)", "14", "14", "14", "12"],
    ["Fourth agent deployed", "14", "14", "14", "14"],
    ["Analysis agent withdrawn", "0", "0", "14", "7"],
    ["Research agent withdrawn", "0", "0", "0", "0"],
  ]),
  caption("Table 5. Teams derived by the task-aware condition with all four agents deployed."),
  table([3300, 3800, 2800], [
    ["Task", "Team derived", "Requirement raised"],
    ["Single-fact retrieval", "research → writer", "—"],
    ["Cross-document synthesis", "research → writer", "—"],
    ["Retrieval with averaging", "research → analysis → writer", "computation"],
    ["Retrieval with addition across documents", "research → analysis → writer", "computation"],
    ["Claim to be checked against corpus", "research → factcheck → writer", "verification"],
    ["Claim that is false as stated", "research → factcheck → writer", "verification"],
    ["Fact absent from corpus", "research → writer", "—"],
  ]),
];

const body4a = [
  p("Adaptivity separates the conditions sharply. Every scenario other than the baseline required modification of source under the static arrangement, forty-two modifications in total across the design, and none under any formed condition. The static arrangement also accounts for all twenty-eight runtime failures observed: because it cannot know that an agent is absent, it discovers the absence by invoking the agent, after other agents have already run and consumed resources."),
  p("Precision is the measure on which the first mechanism was found wanting. Task-blind formation scores 0.705 against the static team's 0.786, and forms larger teams, 3.50 agents against 3.00. The static team's recall, at 0.952, is itself below unity: it never includes the fact-checking agent, so the two tasks requiring a claim to be checked are answered by a team that cannot check one. The cause is visible in the scenario in which a fourth agent is deployed: formation includes that agent because it is eligible, not because any task requires it. Since the mechanism never observes the task, eligibility is the only criterion available to it."),
  p("Separating the two changes made to the mechanism shows where the improvement originates. Loosening the writer agent's declaration, which had previously required conclusions and thereby forced the analysis agent into every chain, raises precision from 0.705 to 0.804 but lowers recall from 0.976 to 0.929. Task-awareness is what carries precision to 1.000 while restoring recall to 1.000, and reduces the mean team to 2.36 agents. Table 5 shows the mechanism at work: teams differ by task, and match the pre-registered requirement sets exactly."),
  p("The most informative result is a reduction in completions. When the analysis agent is withdrawn, the loosened condition completes all fourteen tasks and the task-aware condition completes seven. The lower figure is the correct behaviour. Five of the fourteen tasks require arithmetic the corpus does not state and two require a claim to be checked; with neither an analysis nor a fact-checking agent deployed in that scenario, the loosened condition answers all of them using research and writer alone and reports success, whereas the task-aware condition declines those seven and names the absent capability in each case. The same behaviour appears in the baseline scenario, where the task-aware condition completes twelve of fourteen, declining the two verification tasks because no fact-checking agent is deployed. A system that answers an arithmetic question without an arithmetic agent has not succeeded but has failed silently, and no measure of completion alone distinguishes the two."),

];

const body4b = [
  h1("Discussion"),
  p("Runtime formation removes a genuine defect. A team written in source is an assertion about a deployment, and in a cloud-native environment that assertion decays without warning; formation eliminated every source modification the scenarios would otherwise have required, and converted twenty-eight runtime failures into determinations made before any agent was invoked. That much was expected."),
  p("The more useful discussion concerns the result that was not expected. The mechanism, as first implemented, was less precise than the arrangement it replaced. This was not an implementation defect but a property of the design: formation consulted the capability graph and nothing else, so an agent's eligibility was the whole of its claim to inclusion. Retaining that negative result was instructive, because the diagnosis it forced produced the final mechanism, and because it establishes that the adaptivity gain is not free."),
  p("A second observation deserves emphasis. Before the writer agent's declaration was loosened, arithmetic tasks succeeded under task-blind formation, but not because formation had determined that they required arithmetic. The writer required conclusions, only the analysis agent produced conclusions, and analysis was therefore unavoidable in every chain. The mechanism was working by an accident of how capabilities had been declared. This is worth stating plainly because it is a hazard specific to declaration-driven systems: a sufficiently constrained declaration can conceal the absence of a decision procedure, and the concealment is discovered only when the constraint is relaxed."),
  p("The finding with the broadest implication is that completion is an inadequate measure for these systems. Under withdrawal of the analysis agent, the condition completing more tasks is the condition behaving worse. This aligns with the multi-agent failure literature, in which the largest failure category concerns verification rather than execution, and systems report success while returning unreliable results [ref]. Formation offers a partial defence not available to a static team: because membership is decided before execution and against a stated requirement, a task whose requirements cannot be met is identifiable in advance rather than after the fact."),
  p("Several limitations bound these results. The task profiler is a keyword matcher, chosen so that formation remains free of inference and therefore exactly measurable; it will not generalise to unusually phrased tasks, and a model-based profiler is the natural successor, though it would require a different evaluation design, since composition would cease to be exact and would have to be sampled. The task set comprises fourteen tasks over a four-document corpus. It exercises both requirement markers and separates the conditions, but it does not characterise the profiler's coverage over arbitrary phrasing. Requirement markers are declared by the author of each agent, so a miscategorised agent produces a miscategorised team, and nothing verifies a declaration against behaviour. Withdrawal during execution was tested and is reported above, but only for a process removed outright; an agent that remains reachable while failing to respond was not examined, and detection in that case would depend on timeout configuration rather than on connection refusal. Finally, answer quality under real inference was confirmed to be functional but was not measured, so the effect of team composition on the quality of the final answer remains open."),
  p("Relative to the reviewed literature, the contribution is narrow and deliberately so. No claim is made regarding the deployment of agents on Kubernetes, which the reviewed infrastructure work already addresses, nor regarding the protocols, which are consumed as specified. The claim concerns the step between a discovered set of agents and a working team, which the reviewed work leaves unspecified, and the demonstration that this step admits a measurable criterion beyond feasibility."),

  h1("Conclusions"),
  p("This chapter constructed an agentic multi-agent system communicating over open agent standards and deployed as independent Kubernetes workloads, and replaced its author-defined team with formation performed at run time from capabilities the agents advertise about themselves."),
  p("Three findings emerge. Formation eliminates the coupling between a deployment and the coordinator's source: across four deployment scenarios it required no source modification where the static arrangement required forty-two, and it converted every runtime failure into a determination made before execution. Formation from capability declarations alone is insufficient, and was measurably less precise than the static arrangement it replaced, at 0.705 against 0.786, because eligibility is not necessity. Admitting the task into formation through requirement markers resolves this, reaching precision of 1.000 with perfect recall while reducing the mean team from 3.50 to 2.36 agents."),
  p("The result that best characterises the mechanism is a reduction in completed tasks. When a required capability is absent from the deployment, task-aware formation declines the tasks that need it and names what is missing, where the task-blind arrangement answers them with an inadequate team and reports success. For agentic systems assembled from independently deployed parts, the ability to determine before execution that a task cannot be done appears more valuable than the ability to attempt it."),
];

// references — Vancouver, two columns
const refs = [
  h1("References"),
  new Paragraph({
    spacing: { after: 140 },
    children: [new TextRun({ font: SERIF, size: SMALL, italics: true, text:
      "[Entries 1 and 4-13 were verified on 25 September 2026: titles and full author lists checked against the arXiv record, and entries 13 and 17 resolved through Crossref. DOIs are included. Entries 2, 3, 14-16 and 18 are web resources with no DOI and require access dates. Replace the [ref] markers in the Introduction, Related Works, Table 1 and Discussion with the corresponding numbers in order of first appearance.]" })],
  }),
  ...[
    "Ehtesham A, Singh A, Gupta GK, Kumar S: A survey of agent interoperability protocols: Model Context Protocol (MCP), Agent Communication Protocol (ACP), Agent-to-Agent Protocol (A2A), and Agent Network Protocol (ANP). arXiv:2505.02279. 2025. 10.48550/arXiv.2505.02279",
    "Anthropic: Model Context Protocol specification. 2025. Available from: modelcontextprotocol.io",
    "Google: Agent2Agent (A2A) protocol specification. 2025. Available from: a2a-protocol.org",
    "Li Q, Xie Y: From glue-code to protocols: a critical analysis of A2A and MCP integration for scalable agent systems. arXiv:2505.03864. 2025. 10.48550/arXiv.2505.03864",
    "Jeong C: A study on the MCP x A2A framework for enhancing interoperability of LLM-based autonomous agents. arXiv:2506.01804. 2025. 10.48550/arXiv.2506.01804",
    "Cemri M, Pan MZ, Yang S, et al.: Why do multi-agent LLM systems fail? Advances in Neural Information Processing Systems (NeurIPS). 2025. 10.48550/arXiv.2503.13657",
    "Du H, Su J, Li J, Ding L, Yang Y, Han P, et al.: ProtocolBench: which LLM multi-agent protocol to choose? arXiv:2510.17149. 2025. 10.48550/arXiv.2510.17149",
    "Tran D, Kiela D: Single-agent LLMs outperform multi-agent systems on multi-hop reasoning under equal thinking token budgets. arXiv:2604.02460. 2026. 10.48550/arXiv.2604.02460",
    "Yan W: Don't build multi-agents. Cognition. 2025. Available from: cognition.com/blog/dont-build-multi-agents",
    "Dey R, Viradecha P: Infrastructure for the agentic web: gap analysis and architecture from the Agentverse platform. arXiv:2606.20570. 2026. 10.48550/arXiv.2606.20570",
    "Sharma R, de Vos M, Chari P, Raskar R, Kermarrec AM: Position: collaborative agentic AI needs interoperability across ecosystems. arXiv:2505.21550. 2025. 10.48550/arXiv.2505.21550",
    "Liao CC, Liao D, Gadiraju SS: AgentMaster: a multi-agent conversational framework using A2A and MCP protocols for multimodal information retrieval and analysis. Proc 2025 Conf Empirical Methods in Natural Language Processing (EMNLP): System Demonstrations. 2025. 10.48550/arXiv.2507.21105",
    "Dähling S, Razik L, Monti A: Enabling scalable and fault-tolerant multi-agent systems by utilizing cloud-native computing. Auton Agent Multi-Agent Syst. 2021, 35:10. 10.1007/s10458-020-09489-0",
    "Cloud Native Computing Foundation: Cloud-native foundations for distributed agentic systems. CNCF Technical Oversight Committee initiative, issue 1746. 2026.",
    "Cloud Native Computing Foundation: kagent - bringing agentic AI to cloud native. CNCF Blog. 2025. Available from: kagent.dev",
    "Cloud Native Computing Foundation: Cloud native agentic standards. CNCF Blog. 2026.",
    "Burns B, Grant B, Oppenheimer D, Brewer E, Wilkes J: Borg, Omega, and Kubernetes. Queue. 2016, 14:70-93. 10.1145/2898442.2898444",
    "Kubernetes Authors: Configure liveness, readiness and startup probes. Kubernetes Documentation. 2026.",
  ].map((t, i) =>
    new Paragraph({
      spacing: { after: 70, line: 210 },
      children: [new TextRun({ text: `${i + 1}. ${t}`, font: SERIF, size: SMALL })],
    })),
];

const actions = [
  new Paragraph({
    spacing: { before: 200, after: 140 },
    shading: { type: ShadingType.CLEAR, fill: "FDECEC", color: "auto" },
    border: {
      top: { style: BorderStyle.SINGLE, size: 8, color: "C00000", space: 6 },
      bottom: { style: BorderStyle.SINGLE, size: 8, color: "C00000", space: 6 },
      left: { style: BorderStyle.SINGLE, size: 8, color: "C00000", space: 6 },
      right: { style: BorderStyle.SINGLE, size: 8, color: "C00000", space: 6 },
    },
    children: [new TextRun({ text:
      "AUTHOR ACTION LIST — NOT PART OF THE CHAPTER; DELETE THIS PAGE BEFORE SUBMISSION",
      font: SERIF, size: BODY, bold: true, color: "C00000" })],
  }),
  ...[
    "FIGURES. Figure 1 (formation) is embedded; the editable source is figure_formation.svg. A second figure remains advisable: the system architecture, showing the four agents, the A2A and MCP boundaries and the Kubernetes layer. It is referenced implicitly by the Materials and Methods section and a reader will expect it.",
    "REFERENCES. Entries 1 and 4-13 verified 25 September 2026 against the arXiv record; 13 and 17 resolved through Crossref; DOIs inserted. Two author attributions were found wrong during this check and corrected. Still outstanding: add access dates for the five web resources without DOIs (2, 3, 14-16, 18) and confirm the CNCF URLs, which may have moved. Do not add any further reference without first resolving its DOI or title.",
    "REPLACE THE [ref] MARKERS in the Introduction, Related Works, Table 1 and Discussion with reference numbers in order of first appearance. They are deliberate placeholders, not omissions.",
    "SUPPLY MISSING SETUP DETAIL: Kubernetes distribution and version, container base image and size, the local model used for the end-to-end confirmation, and the corpus size in documents and words. Only the trial counts and results are currently stated.",
    "INSERT AUTHORSHIP: name, affiliation and supervisor as required by the departmental thesis format.",
    "CHECK CHAPTER NUMBERING against the rest of the thesis. Section headings here are unnumbered and may need to become 4.1, 4.2 and so on, with tables and figures renumbered to match.",
    "UNRESPONSIVE-AGENT CASE. Withdrawal by process removal is now tested. The remaining untested failure is an agent that stays reachable but stops responding, where detection depends on timeout configuration. Worth a short run if time permits, since the Limitations section names it.",
  ].map((t, i) =>
    new Paragraph({
      spacing: { after: 90, line: 220 },
      indent: { left: 360, hanging: 260 },
      children: [new TextRun({ text: `${i + 1}.  ${t}`, font: SERIF, size: SMALL })],
    })),
];


const withdrawalText = [
  h2("Withdrawal during execution"),
  p("Every scenario reported above alters the deployment before formation runs, which is the straightforward case: formation simply observes a different set of agents. The harder case is an agent withdrawn after the team has been formed and while it is being executed. Two conditions were compared. Under a fixed plan the team is computed once and followed, which is the behaviour described so far. Under re-formation, a failed call causes the coordinator to re-discover what is still running and re-form from the material already produced rather than from the beginning."),
  p("Two cases were used, chosen because they should behave differently. In the first the withdrawn agent is the only one satisfying a requirement the task raised, so no recovery is possible and the question is only whether that is reported or merely crashed into. In the second a second agent satisfying the same requirement is also deployed, so recovery is possible and the conditions can separate. Results appear in Table 6 and Figure 3."),
];

const table6 = [
  caption("Table 6. Outcome when an agent is withdrawn mid-execution."),
  table([2300, 2300, 2650, 2650], [
    ["Case", "Fixed plan", "Re-forming", "Recovered team"],
    ["Sole satisfier withdrawn", "Aborted at the failed call", "Declined, naming the unsatisfiable requirement", "none exists"],
    ["Alternative agent deployed", "Aborted at the failed call", "Recovered and completed", "compute \u2192 writer"],
  ]),
];

const withdrawalText2 = [
  p("Three things follow. Re-formation converts an abort into either a completed task or a stated reason, which is the same distinction observed between runtime and reported failure in the scenario results. Recovery itself, however, depends on capability-level redundancy rather than on the re-forming mechanism: in the second case an agent able to do the work was running and idle throughout, and the fixed plan failed only because it could not be revised to reach it."),
  p("The third observation is the more interesting, and it qualifies the earlier precision result. Because task-aware formation admits an agent only when something requires it, every member of a formed team is load-bearing by construction. There are no optional members to lose. The precision that makes the team efficient is the same property that leaves it without slack, so any withdrawal from a formed team necessarily breaks a requirement. Redundancy must therefore be supplied by the deployment, through a second agent or a second replica, rather than expected from formation."),
  p("Detection was immediate in all trials, at less than one hundredth of a second, because a withdrawn process refuses the connection outright. This figure should not be generalised: an agent that remains reachable but stops responding would not be detected until a timeout expired, and that case was not tested."),
];

// =========================================================================
const doc = new Document({
  creator: "David Adekoya",
  title: "Runtime Team Formation in a Cloud-Native Multi-Agent System",
  sections: [
    sec(ONE_COL, front),
    sec(TWO_COL, body1),
    sec(ONE_COL, table1),
    sec(TWO_COL, body2a),
    sec(ONE_COL, figureArch),
    sec(TWO_COL, body2b),
    sec(ONE_COL, [...figure1, ...table2]),
    sec(TWO_COL, body3),
    sec(ONE_COL, table3),
    sec(TWO_COL, [...body4a, ...withdrawalText]),
    sec(ONE_COL, [...table6, ...figureWithdraw]),
    sec(TWO_COL, [...withdrawalText2, ...body4b, ...refs]),
    sec(ONE_COL, actions),
  ],
});

Packer.toBuffer(doc).then((b) => {
  fs.writeFileSync("Chapter_RuntimeTeamFormation.docx", b);
  console.log("written: Chapter_RuntimeTeamFormation.docx", b.length, "bytes");
});
