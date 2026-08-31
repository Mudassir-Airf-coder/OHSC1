# Loop Engineering 
Imagine you've been using a coding agent every day like this: you type what you want, it does something, you read the result, and then YOU decide what to type next. That's the whole game right now — you're the engine that keeps it moving. The moment you put your phone down, everything stops. That's called **prompting**, and honestly, most people never leave this stage.

Loop Engineering is about building something that keeps that cycle going **without you** pressing the button every single time. Not because you stop mattering — you still decide _what_ the goal is, and you're still the one who owns it if something goes wrong. Those two jobs — deciding the goal, and being responsible for the outcome — never leave your hands. Everything else, a loop can take over.

## What's actually inside a loop?

Think of a loop like hiring a new employee who works while you sleep. What would that employee need?

- **Something that tells them when to start their shift.** That's called the **heartbeat** — could be a clock (every morning at 9), or an event (the moment a customer emails).
- **Their own desk**, so they don't mess up someone else's papers. That's a **worktree** — a separate copy of the project so two workers never collide.
- **A training manual** for how your team does things — that's a **skill**, written once, read automatically whenever it's relevant.
- **A second person who checks their work** — because if the same employee grades their own homework, they'll always say "looks great!" That's the **maker-checker split**, done with subagents.
- **Actual keys to the building** — not just permission to talk about doing work, but a real way to open a door, send an email, push code. That's a **connector**.
- **A notebook that survives after their shift ends.** This is called the **spine**, and it might be the single most important piece — without it, your new employee wakes up every single day having completely forgotten yesterday, and just starts over from scratch, forever.

You can build this whole setup in Claude Code, where most of it comes ready-made, or in OpenCode, where you wire each piece together yourself with plain scripts. Different toolbox, same six pieces.

## What makes it start?

This is called the **heartbeat**, and there are four flavors:

1. **While you're watching** — it keeps checking every few minutes, but only while your laptop's open. Close it, and it stops. Good for something quick, like watching a deploy finish.
2. **Until it's actually done** — instead of a timer, it keeps trying until a real test proves success. And here's the important bit: the thing deciding "done" is never the same agent doing the work — otherwise it would just declare victory to stop working.
3. **On a real schedule, even if you're asleep** — this is the big one. Every morning at 8:30, whether your laptop is open, closed, or in another country, something wakes up, does the job, and reports back.
4. **The moment something happens** — like a doorbell. Nothing happens until someone rings it (opens a pull request, sends a message), and then it reacts instantly.

## What happens during one single "beat" of work?

Every time the loop fires, four things need to be true. It needs its own private workspace so it doesn't wreck anyone else's files. It needs to already know the project's habits, so you're not re-explaining the same rules every morning. It needs real tools to actually _do_ something — and here's a fun detail: if a tool fails, the error message it gets back matters a lot. "Error 403" teaches it nothing. "You need permission X, go get it" lets it actually fix itself on the next try. And finally, one agent does the work, and a _completely different_ agent checks it — never let the same brain grade its own test.

## The notebook that makes it all work — the spine

Here's the part people forget, and it breaks everything if you skip it. The model itself has zero memory between runs — it's not being lazy, it genuinely doesn't remember anything from yesterday. So you write two things down for it, every time: a **rules file**, for lessons that are always true ("we always squash our commits"), and a **progress file**, for what happened yesterday and what's still unfinished. Think of it like a diary you hand a new substitute teacher every morning — front pages are permanent classroom rules, back pages are "here's exactly where we stopped."

## Staying in charge, even after it's automatic

Two things sneak up on people. First — **cost**. Running the same loop every 5 minutes instead of once an hour isn't 5x more expensive, it can be over 100 times more expensive, for zero extra benefit — frequency is the real cost lever, not the task itself. Second — **just because it says "done" doesn't mean it's actually done**. The checker agreeing is a claim, not proof. You should still glance at the real work sometimes.

And here's the deepest point in the whole topic: building a loop can make you sharper, because you're still reading and understanding the work — or it can make you lazier, because you've stopped looking entirely and just trust the green checkmark. Both people built the exact same loop. Only one of them is still actually understanding their own project six months later.

---

**Next up:** once you have this one trustworthy worker, the next question becomes — what exactly is that worker _allowed_ to do? That's Harness Engineering.