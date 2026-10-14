# Figure Generation Guide

Structural diagrams for empirical papers. These are method/architecture
figures — not result plots. Generate from `method-components.csv` and
domain context; do not invent content.

## 1. When to Generate

| Trigger | Figure type |
|---------|-------------|
| `method-components.csv` has ≥3 components | Method architecture diagram |
| Paper has a problem formulation section | System overview / teaser |
| Method has pipeline stages or data flow | Flowchart / pipeline diagram |
| Problem involves agent/environment loop | MDP / control loop diagram |

## 2. File Organization

- Store TikZ source files in `paper/figures/<name>.tikz`.
- Include in `main.tex` via `\input{figures/<name>.tikz}`.
- All figures must compile standalone with the packages already in the template
  (`tikz`, `arrows`, `positioning`, `fit`, `calc`).

## 3. Style Rules

- Use `\footnotesize` or `\scriptsize` for node text in two-column layouts.
- Color palette (low-saturation, accessible):
  - Novel components: `fill=blue!8, draw=blue!60`
  - Standard components: `fill=gray!8, draw=gray!50`
  - Data/signal flow: `fill=orange!8, draw=orange!60`
  - Environment/external: `fill=green!8, draw=green!50`
- Line widths: `thick` for main flow, `thin` for secondary.
- Arrow style: `->, >=stealth` for data flow; `->, dashed` for optional paths.
- Keep diagrams within `\columnwidth` for single-column figures,
  `\textwidth` for `figure*` double-column figures.

## 4. Pattern: System Overview (fig:teaser)

Purpose: show the problem setting and where the proposed method fits.
Place in Introduction.

**Data source**: domain description + `method-components.csv`.

```latex
\begin{figure}[t]
\centering
\begin{tikzpicture}[
    node distance=0.8cm and 1.2cm,
    block/.style={rectangle, draw, rounded corners, minimum height=0.8cm,
                  minimum width=1.8cm, align=center, font=\footnotesize},
    novel/.style={block, fill=blue!8, draw=blue!60, thick},
    standard/.style={block, fill=gray!8, draw=gray!50},
    env/.style={block, fill=green!8, draw=green!50},
    arr/.style={->, >=stealth, thick},
]
% Environment / problem setting (left side)
\node[env] (env1) {<Component A>};
\node[env, below=of env1] (env2) {<Component B>};
\node[env, below=of env2] (env3) {<Component C>};

% Controller / method (right side)
\node[novel, right=2cm of env2] (method) {<Proposed\\Method>};

% Connections
\draw[arr] (env1.east) -- (method.west |- env1) -- (method);
\draw[arr] (env2) -- (method);
\draw[arr] (env3.east) -- (method.west |- env3) -- (method);
\draw[arr] (method.south) -- ++(0,-0.6) -| node[pos=0.25, below, font=\scriptsize]{control} (env2.south);
\end{tikzpicture}
\caption{System overview: <domain> with <method> controller.}
\label{fig:teaser}
\end{figure}
```

**Adaptation rules**:
- Replace `<Component A/B/C>` with actual physical/data components from the domain.
- Replace `<Proposed Method>` with the method name.
- Add sub-modules inside the method node if they fit, or use a separate
  method-architecture figure for detail.

## 5. Pattern: Method Architecture (fig:method)

Purpose: show internal pipeline — each component from `method-components.csv`
as a box, with data flow arrows. Novel components highlighted.
Place in Method section.

**Data source**: `method-components.csv` columns `name`, `is_novel`,
`input_format`, `output_format`.

```latex
\begin{figure}[t]
\centering
\begin{tikzpicture}[
    node distance=0.6cm and 0.8cm,
    block/.style={rectangle, draw, rounded corners, minimum height=0.7cm,
                  minimum width=2cm, align=center, font=\footnotesize},
    novel/.style={block, fill=blue!8, draw=blue!60, thick},
    standard/.style={block, fill=gray!8, draw=gray!50},
    arr/.style={->, >=stealth, thick},
    darr/.style={->, >=stealth, dashed, gray},
    lbl/.style={font=\scriptsize, midway, above},
]
% Pipeline stages (left to right or top to bottom)
\node[standard] (input) {State\\Observation};
\node[standard, right=of input] (backbone) {RL Backbone};
\node[novel, right=of backbone] (c1) {Module C1\\(novel)};
\node[standard, right=of c1] (output) {Feasible\\Action};

% Optional modules (above/below)
\node[novel, above=0.8cm of backbone] (c2) {Module C2\\(novel)};
\node[novel, below=0.8cm of backbone] (c3) {Module C3\\(novel)};

% Main flow
\draw[arr] (input) -- (backbone);
\draw[arr] (backbone) -- node[lbl]{raw action} (c1);
\draw[arr] (c1) -- (output);

% Optional connections
\draw[darr] (c2) -- node[right, font=\scriptsize]{objective} (backbone);
\draw[darr] (c3) -- node[right, font=\scriptsize]{fallback} (backbone);
\end{tikzpicture}
\caption{Method architecture. Blue-shaded modules are novel contributions.
Dashed arrows indicate optional paths.}
\label{fig:method}
\end{figure}
```

**Adaptation rules**:
- One box per row in `method-components.csv`.
- Use `novel` style for `is_novel=yes`, `standard` for others.
- Arrow labels from `output_format` → next component's `input_format`.
- Ablation switches: add a small "on/off" annotation near novel boxes
  if ablation is mentioned in the paper.

## 6. Pattern: MDP / Control Loop (fig:mdp)

Purpose: show the agent-environment interaction loop with state, action,
reward, and constraints. Common in RL and control papers.

```latex
\begin{figure}[t]
\centering
\begin{tikzpicture}[
    node distance=1.5cm,
    block/.style={rectangle, draw, rounded corners, minimum height=1cm,
                  minimum width=2.5cm, align=center, font=\footnotesize},
    arr/.style={->, >=stealth, thick},
    lbl/.style={font=\scriptsize, fill=white, inner sep=1pt},
]
\node[block, fill=blue!8, draw=blue!60] (agent) {Agent\\(Policy $\pi_\theta$)};
\node[block, fill=green!8, draw=green!50, right=3cm of agent] (env) {Environment};

% Upper path: action
\draw[arr] (agent.north east) -- node[lbl, above]{action $a_t$}
           (env.north west);
% Lower path: state + reward
\draw[arr] (env.south west) -- node[lbl, below]{state $s_{t+1}$, reward $r_t$}
           (agent.south east);

% Constraint box
\node[block, fill=orange!8, draw=orange!60,
      below=0.8cm of $(agent)!0.5!(env)$] (constr) {Constraint\\Module};
\draw[->, >=stealth, dashed] (agent.south) |- (constr);
\draw[->, >=stealth, dashed] (constr) -| (env.south);
\end{tikzpicture}
\caption{MDP formulation with constraint processing.}
\label{fig:mdp}
\end{figure>
```

## 7. Pattern: Flowchart / Pipeline

Purpose: sequential processing steps. Good for data preprocessing,
training pipelines, or evaluation protocols.

```latex
\begin{figure}[t]
\centering
\begin{tikzpicture}[
    node distance=0.5cm,
    step/.style={rectangle, draw, rounded corners, minimum width=3cm,
                 minimum height=0.6cm, align=center, font=\footnotesize,
                 fill=gray!8},
    arr/.style={->, >=stealth, thick},
]
\node[step] (s1) {Step 1: <description>};
\node[step, below=of s1] (s2) {Step 2: <description>};
\node[step, below=of s2] (s3) {Step 3: <description>};
\node[step, below=of s3] (s4) {Step 4: <description>};

\draw[arr] (s1) -- (s2);
\draw[arr] (s2) -- (s3);
\draw[arr] (s3) -- (s4);
\end{tikzpicture}
\caption{Processing pipeline overview.}
\label{fig:pipeline}
\end{figure}
```

## 8. Deriving Figures from method-components.csv

Procedure:
1. Read `notes/design/method-components.csv`.
2. For **fig:method** (method architecture):
   - Create one box per component row.
   - Style: `novel` if `is_novel=yes`, else `standard`.
   - Connect boxes following the pipeline order (input → processing → output).
   - Label arrows with `output_format` values.
   - Add ablation annotations for components with `ablation_priority=high`.
3. For **fig:teaser** (system overview):
   - Group components by role (environment vs controller vs evaluation).
   - Show the boundary between problem setting and proposed solution.
4. Verify figure compiles: `pdflatex main.tex` with no errors in the
   figure region.

## 9. Common Mistakes

- Over-complicated diagrams with too many crossing arrows. Simplify.
- Using `\includegraphics` for diagrams that should be TikZ (not
  version-controllable, resolution issues).
- Forgetting to reference the figure in text (`Figure~\ref{fig:...}`).
- Using saturated colors that are hard to read in print.
- Making figures wider than `\columnwidth` without switching to `figure*`.
