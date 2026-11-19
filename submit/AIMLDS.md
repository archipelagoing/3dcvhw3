# AI, ML, Data Science, Geometry, and Game Theory — Interest Profile

Based on the repositories created since September 1, 2024, your interest is not simply “using AI.” You are drawn to the structure behind intelligence: how information is represented, how competing objectives are reconciled, and how complex data can be made legible through geometry and interactive visual tools.

## The through-line: intelligence as structure, not just output

Several projects look beneath an AI system’s final answer. `Situationion` asks where relational, causal, temporal, and event information is recoverable inside a transformer. `LongTermMemoryLLM` treats useful AI memory as an organized retrieval and graph problem rather than a chat-history dump. `CoalitionMind` and `CognitiveRoutingDegradation` frame cognition as coordination among internal agents over a shared model of the world.

That suggests a particular interest in **representations and mechanisms**:

- What information exists inside a model, and at what layer or location?
- How can a system remember, retrieve, and connect knowledge over time?
- How do multiple perspectives, agents, or tasks become one coherent action?
- What kinds of structure can be measured rather than merely narrated?

This is a research-oriented AI interest. You appear more interested in making systems inspectable and principled than in treating a model as an opaque API.

## Geometry is a recurring way you think

Geometry is not incidental in this portfolio; it is one of your preferred languages for making difficult systems understandable.

### Geometry of meaning and learning

`Subcore-Dynamics-AI` represents research papers as points in semantic embedding space, then studies how clusters emerge, die, merge into a dominant core, or become durable subfields. This is a geometric view of intellectual change: meaning is not only text or labels, but position, density, distance, movement, and neighborhood in a latent space.

`Situationion` similarly examines the geometry of transformer representations: whether controlled changes in a situation alter representations in measurable ways across layers, token positions, and probes. The underlying instinct is to ask whether a model’s internal space has a shape that reflects relationships in the world.

### Geometry as exploratory data analysis

`PCACloud` turns a spreadsheet into a navigable point cloud using PCA and t-SNE. Rather than making dimensionality reduction a static report, it makes projected structure something a person can rotate, inspect, and question. `NormalDistributionVisualizer` does something analogous for statistics: it translates probability mass, standard deviations, tails, and percentages into linked visual objects.

Your data-visualization interest therefore seems educational as well as analytical. You like visualizations that reveal *why* a quantity behaves as it does, not only dashboards that report a number.

### Physical geometry and computer vision

The 3D-computer-vision work (`3dcv`, `3dcompvis`, `3dcvA2`, and coursework) extends the same instinct into physical space: stereo correspondence, depth, point clouds, plane fitting with RANSAC, and projective warps. Here geometry is the bridge between images and a model of the world. Together with the embedding projects, this shows interest in both kinds of geometry:

- **Euclidean/projective geometry** for seeing and reconstructing physical scenes.
- **Latent/high-dimensional geometry** for organizing data, language, and models.

## Game theory is your framework for conflict and coordination

Your game-theory work is especially closely connected to your ML work. In `GTFinalProject` and `EvoNashMTL`, multi-task learning is treated as a bargaining problem: tasks generate gradients that can agree, partially conflict, or compete for influence over shared parameters. Nash bargaining provides a fairness principle for combining those preferences instead of allowing one convenient or high-gradient task to dominate.

`EvoNashMTL` goes a step further by adding replicator-style scheduling. This introduces an evolutionary question: not only how should tasks compromise at a single update, but how should their influence adapt over the course of learning?

That is a distinctive interest: you treat optimization as a **social decision process among objectives**, not merely as numerical minimization. You seem drawn to questions such as:

- How should a shared system allocate influence fairly?
- When is a short-term compromise different from a stable long-term strategy?
- How can one model retain diverse capabilities without letting easy objectives crowd out harder or less frequent ones?
- Can agent-level incentives, bargaining, and evolutionary dynamics explain or improve learning behavior?

The same pattern appears beyond explicit game theory. `CoalitionMind` uses multiple agents negotiating over a shared concept graph; `CognitiveRoutingDegradation` studies selective consultation under constrained conditions; and the multi-agent framing recurs in your AI research. Game theory is therefore not a separate academic topic in your work—it is a general lens for reasoning about intelligence under competing interests and limited resources.

## Your data-science style

Your projects suggest that you value a full chain of reasoning:

1. Formulate a question that is concrete enough to test.
2. Choose a representation that exposes useful structure.
3. Build a measurable model, baseline, or controlled comparison.
4. Visualize results so that a human can inspect the mechanism.
5. Be explicit about uncertainty, controls, and what the evidence does *not* establish.

Examples include probing controls in `Situationion`, held-out evaluation in `CAFA6`, NDCG-based retrieval comparisons in `elastic-benchmarking`, and interactive exploration in `PCACloud`. This is closer to experimental and explanatory data science than to one-off prediction contests.

## Concise description

You are interested in **geometric, interpretable, and game-theoretic approaches to intelligence**. You use geometry to understand both physical scenes and high-dimensional representations; use game theory to reason about fairness, conflict, and adaptation among tasks or agents; and use data visualization to make abstract statistical and machine-learning structure visible, testable, and teachable.

Your strongest recurring themes are:

- representation learning and transformer interpretability;
- embedding spaces, clustering, dimensionality reduction, and semantic geometry;
- multi-task learning, bargaining, evolutionary dynamics, and multi-agent systems;
- 3D vision and the geometry connecting images to the physical world;
- research-grade evaluation paired with intuitive interactive explanation.

## Mathematical view of the interests

### Representation geometry

For an input (x), a neural network layer can be viewed as a map

\[
h_\ell(x) = f_\ell \circ f_{\ell-1} \circ \cdots \circ f_1(x) \in \mathbb{R}^{d_\ell}.
\]

The central interpretability question in `Situationion` is not merely whether a
model produces the right text. It is whether a semantic intervention
\(x \mapsto x'\) induces a meaningful displacement

\[
\Delta_\ell(x,x') = h_\ell(x') - h_\ell(x),
\]

and whether this displacement encodes the changed relation rather than a
superficial lexical change. A controlled probe can ask whether a readout
\(g_\ell\) predicts a variable (y), for example a causal role or temporal
relation:

\[
\hat y = g_\ell(h_\ell(x)), \qquad
\text{score}(g_\ell) \gg \text{score}(\text{lexical control}).
\]

The appealing scientific question is therefore: what is the geometry of a
concept? Is it a direction, a local neighborhood, a nonlinear manifold, or a
relation that only becomes decodable under a particular task and readout?

For `PCACloud`, a centered data matrix \(X \in \mathbb{R}^{n\times d}\) is
projected onto principal axes obtained from

\[
\Sigma = \frac{1}{n-1}X^\top X = V\Lambda V^\top,
\qquad Z_k = XV_k.
\]

The first \(k\) columns of \(V\) maximize retained variance under an
orthogonality constraint. t-SNE instead emphasizes preservation of local
neighbor probabilities, typically by minimizing

\[
\mathrm{KL}(P\|Q) = \sum_{i\ne j} p_{ij}\log\frac{p_{ij}}{q_{ij}}.
\]

Your interest seems to include the productive tension between global structure
(PCA) and local-neighborhood structure (t-SNE), and the question of when either
projection is faithful enough to support a conclusion.

### Multi-task learning as bargaining geometry

In multi-task learning, task losses \(L_1(\theta),\ldots,L_m(\theta)\) induce
task gradients

\[
g_i = \nabla_\theta L_i(\theta).
\]

Conflict can be measured geometrically through

\[
\cos\angle(g_i,g_j) = \frac{g_i^\top g_j}{\lVert g_i\rVert\lVert g_j\rVert}.
\]

Negative cosine similarity means that descending one task can increase another
task's loss. This makes the update direction a coordination problem rather than
a simple average. A weighted update has the form

\[
g(\theta) = \sum_{i=1}^m w_i g_i,
\qquad w_i\ge0,\quad \sum_i w_i=1.
\]

Nash-style multi-task learning asks for weights that preserve a fair balance of
task improvements, rather than weights chosen only for aggregate loss reduction.
Abstractly, if \(u_i(w)\) is the improvement or utility offered to task \(i\), a
Nash bargaining solution seeks

\[
w^* = \arg\max_{w\in\Delta^{m-1}} \prod_{i=1}^m\big(u_i(w)-d_i\big),
\]

or equivalently maximizes the sum of log gains

\[
\max_w \sum_{i=1}^m \log\big(u_i(w)-d_i\big),
\]

where \(d_i\) is a disagreement baseline. This is why your ML and game-theory
interests fit naturally: the Pareto frontier is a geometric object, while
bargaining supplies a normative rule for choosing a point on it.

The evolutionary component of `EvoNashMTL` adds dynamics. A stylized replicator
update for task influence \(w_i\) is

\[
\dot w_i = w_i\big(r_i(w)-\bar r(w)\big),
\qquad \bar r(w)=\sum_jw_jr_j(w).
\]

The question is no longer only “what is fair now?” but “what allocation is
stable, adaptive, and non-collapsing over time?” That is a sophisticated bridge
from local gradient geometry to long-run strategic dynamics.

### Camera geometry and visual-hull reconstruction

Your current CS 532 assignment adds a concrete geometric counterpart. A
calibrated camera is represented by a projective matrix

\[
P_i = K_i[R_i\mid t_i] \in \mathbb{R}^{3\times4},
\qquad \tilde x_i \sim P_i\tilde X,
\]

where \(\tilde X=[X,Y,Z,1]^\top\) is a world point and
\(\tilde x_i=[\tilde u_i,\tilde v_i,\tilde w_i]^\top\) is a homogeneous image
point. Dehomogenization gives

\[
u_i=\frac{\tilde u_i}{\tilde w_i},\qquad
v_i=\frac{\tilde v_i}{\tilde w_i}.
\]

Every silhouette pixel back-projects to a generalized cone. With binary
silhouette \(S_i\), the visual hull is the intersection

\[
\mathcal V = \bigcap_{i=1}^N
\left\{X:\ \pi(P_i\tilde X)\in S_i\right\}.
\]

On a discrete grid, for a voxel center \(c_v\), this becomes

\[
\operatorname{occupied}(v)=
\bigwedge_{i=1}^N
\left[
\tilde w_i>0\ \land\ (u_i,v_i)\in\Omega_i\ \land\ S_i(u_i,v_i)=1
\right].
\]

This is a particularly good match for your broader interests: a high-dimensional
or latent-space intersection becomes an explicit 3D set, and the limits of the
representation are mathematically visible. Concavities not expressed in any
silhouette cannot be recovered, so generally

\[
\mathcal O_{\text{true}}\subseteq\mathcal V,
\]

with equality only under favorable viewing and shape conditions.

For true-color fusion, visibility is a ray-geometry problem. If \(q\) is an
exposed surface point and \(C_i\) is a camera center, inspect the segment

\[
r_i(t)=q+t(C_i-q),\qquad 0<t<1.
\]

Camera \(i\) contributes a color only if no occupied voxel lies along this open
segment. A robust color estimate can then use the per-channel median over valid
views:

\[
\mathbf c(q)=\operatorname{median}_{i\in\mathcal V(q)}\mathbf I_i\big(\pi(P_i\tilde q)\big).
\]

This connects projective geometry, discretization error, occlusion, robust
statistics, and appearance reconstruction in a single pipeline.

## Questions you are likely to enjoy pursuing

The following questions follow naturally from the mathematical patterns in your
repositories and from the camera/voxel assignment.

1. **How does camera placement change recoverability?** Given fixed camera
   centers \(C_i\), can one quantify the unobservable volume
   \(\operatorname{Vol}(\mathcal V\setminus\mathcal O_{\text{true}})\), and choose
   a new view that maximally reduces it? This is an active-view-planning problem.

2. **What is the resolution-error law for a visual hull?** If voxel widths are
   \((\Delta x,\Delta y,\Delta z)\), how do memory \(O(N_xN_yN_z)\), runtime,
   surface roughness, and geometric error scale as the grid is refined? When is
   an adaptive octree superior to a uniform grid?

3. **Can silhouette consistency be made probabilistic?** Instead of the hard
   Boolean intersection, estimate occupancy using
   \[
   p(v\mid S_{1:N})\propto p(v)\prod_i p\big(S_i(u_i,v_i)\mid v\big),
   \]
   which would express uncertainty from calibration error, segmentation noise,
   and pixels near silhouette boundaries.

4. **How should multi-view color be weighted?** Median fusion is robust, but a
   physically or geometrically informed estimator might use a view angle,
   distance, and visibility confidence weight, such as
   \[
   \hat{\mathbf c}(q)=\frac{\sum_i w_i(q)\mathbf c_i(q)}{\sum_iw_i(q)},
   \quad w_i\propto\max(0,n(q)^\top\hat d_i)^\alpha.
   \]
   When does this improve appearance, and when does it amplify calibration or
   reflectance errors?

5. **Can game theory choose camera views or sensor budgets?** Treat each camera
   or region of the object as an agent with competing coverage needs. What
   allocation of a finite view, compute, or annotation budget yields fair
   uncertainty reduction across regions, rather than excellent coverage of only
   the easiest surfaces?

6. **Is latent-space geometry predictive of physical or causal geometry?** If
   a model embeds images, captions, actions, or events, when do distances in
   embedding space correspond to 3D pose, causal role, or temporal structure?
   What controls distinguish true structure from shortcut features?

7. **How do coordination failures appear geometrically?** In multi-task
   learning, can the changing Gram matrix \(G_{ij}=g_i^\top g_j\) predict task
   collapse, cycling, or domination before final accuracy deteriorates?

8. **Can a visual hull be treated as a shared world model for agents?** A
   multi-agent system could maintain competing hypotheses over 3D occupancy,
   camera reliability, and object appearance. How should the agents bargain over
   an update when their evidence conflicts?

## What the CS 532 assignment can actually answer

The questions above include research directions that require additional data,
algorithms, or experiments. The voxel-reconstruction assignment itself can
answer the following narrower questions. These answers are not speculative: they
follow from the calibrated multi-view silhouette model and the required
reconstruction pipeline.

### 1. What 3D shape is identifiable from calibrated binary silhouettes?

**Answer:** The assignment identifies the **visual hull**:

\[
\mathcal V = \bigcap_{i=1}^{8}
\left\{X:\pi(P_i\tilde X)\in S_i\right\}.
\]

This is the set of 3D points whose projections lie inside every foreground
silhouette. It is a conservative outer approximation of the object:

\[
\mathcal O_{\mathrm{true}}\subseteq\mathcal V.
\]

It does **not** identify concavities or interior structure that never change a
silhouette. Therefore, even a perfectly implemented algorithm cannot recover
every feature of the dancer from these measurements alone. The assignment
answers a fundamental representation question: a representation determines both
what can be recovered and what is permanently ambiguous.

### 2. How do multiple cameras reduce ambiguity?

**Answer:** Each valid silhouette is an additional constraint. If
\(\mathcal V_k\) is the feasible volume after \(k\) cameras, then

\[
\mathcal V_{k+1}=\mathcal V_k\cap C_{k+1}
\subseteq\mathcal V_k,
\]

where \(C_{k+1}\) is the generalized cone back-projected from camera
\(k+1\)'s silhouette. Thus, adding a camera cannot enlarge the visual hull;
it can only leave the estimate unchanged or remove unsupported volume.

An answer that can be measured in the submitted implementation is the marginal
constraint supplied by a view:

\[
\Delta N_k=N_{\mathrm{occupied}}(k-1)-N_{\mathrm{occupied}}(k).
\]

A large \(\Delta N_k\) means that view eliminated much ambiguity. This is a
concrete version of the more general question, “Which source of evidence adds
information rather than redundancy?”

### 3. When does agreement among all measurements still fail to establish truth?

**Answer:** Agreement establishes consistency with the measurement model, not
identity with the real object. A voxel can project inside all eight silhouettes
and still occupy empty real space. Formally,

\[
\left(\forall i,\;S_i(\pi(P_i\tilde X))=1\right)
\centernot\implies X\in\mathcal O_{\mathrm{true}}.
\]

The visual hull's filled-in concavities are the direct counterexample. This
gives you an answer relevant to model evaluation and interpretability: passing
every available test does not prove that a representation contains the whole
causal structure of what it models.

### 4. How does voxel resolution change the reconstruction?

**Answer:** Resolution is a bias-compute tradeoff. With a bounding box of side
lengths \(L_x,L_y,L_z\), voxel widths are

\[
\Delta x=\frac{L_x}{N_x},\qquad
\Delta y=\frac{L_y}{N_y},\qquad
\Delta z=\frac{L_z}{N_z},
\]

and the grid contains

\[
N=N_xN_yN_z
\]

candidate voxels. The required silhouette test costs approximately
\(O(8N)\) before ray visibility is considered. Finer grids can approximate a
boundary more closely but use more memory and work; they also make calibration,
silhouette-edge, and rounding errors more visible. The assignment lets you
measure occupied- and surface-voxel fractions across resolutions, which is a
small but real convergence/sensitivity study.

### 5. Why is visibility necessary before combining true colors?

**Answer:** Pixel agreement is not enough for appearance reconstruction. A rear
surface point can project onto a foreground pixel whose color belongs to a
nearer, occluding part of the dancer. Camera \(i\)'s color is admissible only
when the open segment from surface point \(q\) to camera center \(C_i\) is
unblocked:

\[
r_i(t)=q+t(C_i-q),\qquad 0<t<1.
\]

If a ray traversal encounters an occupied voxel on this segment, the view must
not contribute. The answer is that **evidence must be conditioned on whether
the source could actually observe the target**. This is an unusually clear
physical analogue of source reliability in multi-agent systems or task-specific
gradient validity in multi-task learning.

### 6. Why use the median for multi-view color fusion?

**Answer:** The per-channel median has a (50\%\) breakdown point: fewer than
half the samples may be arbitrarily corrupted without driving the median
arbitrarily far. For valid camera color samples \(c_1,\ldots,c_m\), the
assignment uses

\[
\hat c_{\mathrm{median}}=\operatorname{median}(c_1,\ldots,c_m)
\]

per RGB channel, rather than

\[
\hat c_{\mathrm{mean}}=\frac{1}{m}\sum_{j=1}^mc_j.
\]

That makes the reconstruction less vulnerable to a silhouette-edge sample, a
small calibration error, or one poor view. The homework answers a broad
aggregation question: robust consensus is often better than unqualified
averaging when some otherwise plausible observations are wrong.

### 7. How can a representation make errors interpretable?

**Answer:** The false-color point cloud maps position to color:

\[
R=255\frac{X-X_{\min}}{X_{\max}-X_{\min}},\quad
G=255\frac{Y-Y_{\min}}{Y_{\max}-Y_{\min}},\quad
B=255\frac{Z-Z_{\min}}{Z_{\max}-Z_{\min}}.
\]

This does not recover the dancer's appearance; it constructs a diagnostic
encoding. If an axis is flipped, scaled incorrectly, or displaced, the color
field makes the geometric failure visible. The answer is that a good
representation can expose failure modes that raw numerical output would hide.
This is directly transferable to control tasks and probes in transformer
interpretability.

### 8. What is the common question shared with the rest of the portfolio?

**Answer:** The assignment makes the common question precise:

\[
\boxed{\text{Given the observations and representation available, what is
identifiable, what is robustly inferable, and what remains ambiguous?}}
\]

In this assignment, the observations are images and silhouettes, the
representation is a calibrated voxel grid, and the unresolved ambiguity is
mostly concavity and occluded appearance. In `Situationion`, the observations
are model activations and controlled text examples; in `PCACloud`, they are
projected data coordinates; and in `EvoNashMTL`, they are competing task
gradients. The mathematical objects differ, but the intellectual workflow is
the same: state the representation, characterize its constraints, test what its
measurements support, and avoid claiming more than they identify.

## Questions most relevant to `Situationion`

These questions translate the visual-hull assignment's lessons about projection,
constraints, and ambiguity into transformer representation analysis.

### S1. Is a semantic variable encoded, or merely decodable by a flexible probe?

Let \(h_\ell(x)\) be a layer representation and \(y\) a situation variable.
High probe accuracy,

\[
\operatorname{Acc}(g_\ell(h_\ell(x)),y)\gg\operatorname{chance},
\]

shows that \(y\) is decodable under the chosen readout; it does not by itself
show that the model uses \(y\) causally. This resembles visual-hull occupancy:
silhouette consistency is evidence for feasibility, not proof of the true 3D
object. The relevant next question is whether the result survives lexical,
position, and distributional controls.

### S2. Which changes in language produce the intended changes in representation?

For a controlled pair \((x,x')\), define

\[
\Delta_\ell=h_\ell(x')-h_\ell(x).
\]

If \(x\) and \(x'\) differ only in a causal, temporal, or participant-role
relation, does \(\Delta_\ell\) separate reliably from the displacement caused
by a meaning-preserving paraphrase? This is analogous to asking whether a new
camera removes unsupported 3D volume or merely repeats an existing view.

### S3. Where does the information live, and is that location stable?

For a score \(s_{\ell,p}\) across layers \(\ell\), positions \(p\), readouts,
and evaluation splits, ask whether a robust region exists:

\[
(\ell^*,p^*)=\arg\max_{\ell,p}s_{\ell,p}.
\]

Or does the apparent effect depend heavily on measurement choice? A point can
be visible in one camera, occluded in another, and unrecoverable from a poor
view. A transformer claim should likewise report layer, token, probe, and split,
not only its best score.

### S4. What cannot be inferred from the available evaluation set?

Even a strong in-distribution probe cannot establish compositional or causal
generalization. The counterpart of a silhouette-hidden concavity is a semantic
distinction absent from the contrast set. Which counterfactuals make a lexical
shortcut fail while preserving the target relation? Without them, apparent
success remains underidentified.

### S5. Can representation differences predict behavior differences?

If a direction \(d\) appears to encode a relation, test an intervention
\(h_\ell\leftarrow h_\ell+\alpha d\). Does a downstream decision change
systematically with \(\alpha\)? This moves from observational decodability
toward causal use, just as a 3D reconstruction must be checked by reprojection
rather than trusted only because its voxel tests passed.

## Questions most relevant to `EvoNashMTL`

These questions translate multi-view evidence fusion into task-gradient
coordination, bargaining, and long-run adaptive weighting.

### E1. Which task gradients contain genuinely conflicting information?

For task gradients \(g_i=\nabla_\theta L_i\), examine the Gram matrix

\[
G_{ij}=g_i^\top g_j
\]

and normalized alignment

\[
\rho_{ij}=\frac{g_i^\top g_j}{\lVert g_i\rVert\lVert g_j\rVert}.
\]

If \(\rho_{ij}<0\), task updates locally conflict. This is the gradient-space
analogue of camera views that cannot all contribute equally to the color of an
occluded surface point: an unqualified average may combine individually valid
signals into a bad update.

### E2. What makes a task-weight allocation fair rather than merely efficient?

With weights \(w\in\Delta^{m-1}\), the shared update is

\[
g(w)=\sum_{i=1}^m w_i g_i.
\]

Minimizing an aggregate loss may repeatedly privilege easy or high-magnitude
tasks. A bargaining objective instead asks for balanced gains relative to a
baseline \(d_i\):

\[
w^*=\arg\max_{w\in\Delta^{m-1}}\sum_{i=1}^m\log(u_i(w)-d_i).
\]

The relevant question is whether this choice improves worst-task loss,
normalized gain, or Pareto efficiency—not merely mean validation performance.

### E3. When should a task's influence change over training?

If \(r_i(t)\) is a task's current learning value, a replicator-style scheduler
uses

\[
\dot w_i=w_i(r_i-\bar r),\qquad \bar r=\sum_jw_jr_j.
\]

The substantive question is how to define \(r_i\): recent loss decrease,
generalization gain, uncertainty, gradient conflict, or underperformance. The
camera-assignment parallel is visibility gating: a source should influence the
estimate according to whether it is informative for the target now, not simply
because it exists.

### E4. Does adaptation produce stable specialization or winner-take-all collapse?

Track the weight trajectory \(w(t)\). A desirable scheduler should avoid

\[
\exists i:\; w_i(t)\to1\quad\text{and}\quad w_j(t)\to0\ \forall j\ne i
\]

unless an explicit task-completion policy justifies it. Compare weight entropy

\[
H(w)=-\sum_iw_i\log w_i
\]

with task-level validation curves and Pareto-front movement. Does evolution
maintain useful diversity, or merely create a new form of domination?

### E5. Which ablations distinguish bargaining from a convenient heuristic?

Compare uniform weights, static learned weights, Nash-MTL alone, evolutionary
scheduling alone, and the combined method. If \(M\) is a multi-task metric, an
interaction-style comparison is

\[
\big[M(\mathrm{Nash+Evo})-M(\mathrm{Nash})\big]
-\big[M(\mathrm{Evo})-M(\mathrm{uniform})\big].
\]

This asks whether the combined method contributes beyond its ingredients. It is
the same discipline as using controlled silhouette, visibility, and reprojection
checks rather than assuming a plausible 3D output proves the full pipeline.

## Assignment experiment: auditing distributed inference

### Question

> Given several partial signals flowing through a sequence of transformations
> and constraints, which information survives, which is discarded, which signals
> are relevant, and what ambiguities remain even after all evidence is combined?

### Answer through the voxel-reconstruction assignment

The assignment can answer this question by treating visual-hull reconstruction
as an instrumented inference pipeline rather than producing only one final PLY
file. Begin with every voxel in the known bounding box \(B\) as a possible part
of the object:

\[
\mathcal V_0=B.
\]

For camera \(i\), project each surviving voxel center \(c_v\) with \(P_i\) and
retain it only when the projected location lies in that camera's foreground
silhouette:

\[
\mathcal V_i=
\left\{
v\in\mathcal V_{i-1}:\pi(P_i\tilde c_v)\in S_i
\right\}.
\]

The eight camera images are the partial signals. Projection, silhouette lookup,
and intersection are the transformations and constraints. Saving the state after
each camera makes the entire process inspectable.

#### What information survives?

Save the intermediate occupancy volume \(\mathcal V_i\) and its count

\[
N_i=|\mathcal V_i|
\]

after every camera. The surviving voxels are the 3D hypotheses still consistent
with cameras \(1,\ldots,i\). Intermediate PLY files or renders make the
progressive shrinkage of the feasible shape visible.

#### What information is discarded?

For each camera, record the newly eliminated set

\[
D_i=\mathcal V_{i-1}\setminus\mathcal V_i.
\]

These voxels were plausible before camera \(i\), but camera \(i\) ruled them
out. The size

\[
|D_i|=|\mathcal V_{i-1}|-|\mathcal V_i|
\]

is the amount of current ambiguity removed by that view.

#### Which signals are relevant?

Measure a camera's marginal constraint as

\[
r_i=
\frac{|\mathcal V_{i-1}|-|\mathcal V_i|}{|\mathcal V_{i-1}|}.
\]

A large \(r_i\) means the camera supplies substantial new constraint; a value
near zero means the view is mostly redundant with earlier views. Relevance can
also be local: a camera might add little globally but be the only useful view of
an arm, profile, or other particular region.

For true color, relevance is point-specific. Camera \(i\) contributes a color
to surface point \(q\) only if the open camera ray

\[
r_i(t)=q+t(C_i-q),\qquad 0<t<1,
\]

does not cross another occupied voxel. Thus, a camera may be useful for global
shape while being irrelevant for the appearance of a hidden surface point.

#### What remains ambiguous after all evidence is combined?

After all eight silhouettes,

\[
\mathcal V_8=\bigcap_{i=1}^{8}C_i
\]

is the final visual hull: the set of 3D points consistent with every silhouette
cone \(C_i\). It is not guaranteed to equal the true object:

\[
\mathcal O_{\mathrm{true}}\subseteq\mathcal V_8.
\]

The remaining ambiguity is material that silhouettes cannot distinguish—most
notably concavities and hidden interior geometry. Without a ground-truth 3D
model, the assignment cannot measure every false-positive voxel, but it can
identify why such uncertainty is unavoidable: the input representation discarded
that information before reconstruction began.

#### How to validate the answer

Produce the following artifacts in addition to the final reconstruction:

1. Eight intermediate occupancy PLY files or renders, one after each camera.
2. A table containing \(N_i\), \(|D_i|\), and \(r_i\) for every camera.
3. Per-camera images or masks showing the regions each view eliminates.
4. The final false-color and true-color visual hulls.
5. For each output surface point, the number of cameras that passed visibility.
6. Reprojections of the final reconstruction into all input cameras, compared
   against their original silhouettes.

This creates an auditable history of inference rather than only a final shape.
It is the precise assignment-level analogue of tracing whether relational
information in a transformer remains available, is filtered out, is relevant to
a particular output, or stays fundamentally ambiguous.
