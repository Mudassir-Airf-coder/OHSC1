# Harness Engineering

Okay so you've got a loop now — a worker that runs by itself. But here's a scary question: what actually stops it from doing something dumb at 3am when nobody's watching? A model on its own is just raw intelligence. It needs a car built around the engine — brakes, mirrors, a seatbelt — before you'd trust it to drive itself anywhere. That "car built around the engine" is called the **harness**. The simple formula: **Agent = Model + Harness**.

## Two kinds of harness, and only one you control

Some of the harness is built for you — the model's own way of handling its memory, calling tools — you can pick it, but you can't rewrite it. That's the **inner harness**. Everything else — the rules you write, the permissions you set, the checks that run automatically — that's the **outer harness**, and it's entirely yours to shape. This actually solves an argument people have constantly: "should I just write a longer, more careful prompt?" If the problem is about what the agent is _allowed_ to do, a longer prompt won't fix it. A rule will.

## The one sentence that explains almost everything in this topic

**A guardrail belongs in the harness, never in the prompt.** Telling an agent "please don't touch the .env file" is like putting up a polite sign instead of a fence. A model _can_ ignore a sign. It cannot ignore a rule that's actually enforced in the system.

Everything in harness engineering is really just five jobs, done well: **limiting** what it can do, **informing** it what it needs to know, **checking** its work before trusting it, **fixing** mistakes so they don't repeat, and **calling a human** when it's genuinely unsure.

## Building the fence

Start with **permission rules** — three simple buckets. Some actions are automatically fine (reading a file). Some need a human "yes" first, like a doorbell (pushing to a branch). And some are simply never allowed, no matter what — a wall (deleting production data). You sort these by how bad it would be if it went wrong, not by how often it happens.

But even perfect rules aren't fully safe, because someone could hide a sneaky instruction somewhere the agent reads — inside a GitHub issue title, for example — trying to trick it into doing something you never asked for. This is where a **sandbox** saves you: even if the agent gets tricked into _trying_ something bad, if it has no network access at all, there's simply nowhere for it to send stolen data. The trick works, but it fails anyway, because the walls don't care about intentions.

## Making sure it actually knows what it needs to know

A lot of "the AI did something dumb" moments aren't really intelligence problems — they're information problems. If your agent keeps using the wrong tool for your project, that's not a smarter-prompt problem, it's a missing-information problem: write it into the rules file once, and it's fixed forever, every future run. And there's a whole design skill here worth knowing: writing tool descriptions and error messages _for the agent_, the same way apps are designed for humans. A vague error message wastes an entire attempt. A specific one — "you need X permission, go get it" — lets the agent fix itself immediately on the next try.

## Making the checking automatic, not optional

You can write code that runs _automatically_ at key moments — after every file edit, run the linter, no exceptions, the agent can't skip it even if it "forgets." These are called **hooks**. And when a checker gives its verdict, force it into a strict format like PASS/FAIL in fixed JSON — never let it ramble "well, this mostly seems okay" — because a strict shape can be automatically trusted by code, and a rambling opinion can't.

When something does go wrong, don't just patch tonight's problem — ask _why_ it happened, using four buckets: did it not know something (fix the information), did it do something forbidden (fix a permission), was bad work accidentally approved (fix the checker), or did it plan the steps in a bad order (break the task smaller)? And here's the real craft: every time you catch a mistake, turn it into a rule that makes that exact mistake **impossible to happen again**. This turning-mistakes-into-permanent-fixes idea is called the ratchet — it only tightens, never loosens, and it's how a harness quietly gets smarter every week without you doing anything extra.

## Not disappearing once it's running

Here's something people miss: if a rule blocks something and you never see it happen, you learn absolutely nothing from it. A guardrail that fires silently is basically useless — you want every block to show up somewhere loud, because the thing it blocked at 3am might be the most important event of your whole week.

And one final honest warning: **you can over-tighten a harness.** Every single rule you add also removes a move the agent could've made — including the clever, unexpected, actually-correct move. Add too many rules and you end up with a very safe agent that can't do anything interesting anymore. Worse, rules that are shaped around one specific model's quirks quietly break the moment you switch models. So the real skill isn't "add more rules forever" — it's knowing exactly when to stop.

---

**Next up:** once you trust one worker inside its own fence, the next problem shows up the moment you have _several_ workers — how do they all remember things together? That's Graph Engineering.