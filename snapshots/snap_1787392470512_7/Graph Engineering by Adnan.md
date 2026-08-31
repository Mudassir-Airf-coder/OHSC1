# Graph Engineering 

Here's a problem that only shows up once things are going well. You built one loop, it's trustworthy, it's fenced in properly with a good harness — so naturally, you build a second one. Then a third. Then one busy afternoon you fire off twenty agents at once to check twenty different files. And then something annoying happens: two of those agents discover the *exact same bug*, independently, an hour apart, because neither one had any idea the other existed. A simple notes file worked great for one worker. It falls apart completely the moment you have a team.

The whole idea of Graph Engineering fits in one sentence: **the agent forgets everything, but the memory itself doesn't have to.**

## What even is a "graph" here?

Don't overthink the word. A graph is just two things: **points** (called nodes — a person, a fact, a piece of code, a claim) and **arrows between them** (called edges, and the direction matters). "Vendor X *supplied* Component Z" is a tiny graph — one arrow, pointing one way, with a specific meaning. The magic is that unlike a paragraph of text, a computer can actually *follow* that arrow automatically to find everything else connected to it.

And there are really two totally separate kinds of memory you need, and mixing them up causes real trouble:

- **A memory of work done** — like a diary of every experiment you tried, whether it succeeded or failed. This one's basically guaranteed accurate, because it's just recording what actually happened.
- **A memory of facts believed** — like "this API rejects old dates." This one is a *claim*, and claims can be wrong, so every single one needs a source attached — proof of how you know it.

## How the facts actually get written down

First, a cheap model reads through documents and pulls out structured little facts, instead of you manually tagging anything. Then comes the tricky part: the same real thing can show up under different names — "Buzz Aldrin" and "Edwin Aldrin" are the same person, but two people who happen to share a similar name are absolutely *not* the same person just because the spelling looks close. Merging two different things together by mistake is one of the worst failures here, so it's always done carefully, with a confidence score, and kept easy to undo.

And every single fact needs a receipt. A claim with no source attached to it is really just a rumor, dressed up to look official because it's sitting inside a nice organized system. "Nothing in here is unattributed, and nothing in here can't be double-checked" — that's the actual promise a good graph makes, and it's a smaller promise than "everything in here is true." It's not a truth machine. It's an honesty machine.

## Why this changes how "checking work" feels

Without a graph, a reviewer can only say something like "hmm, this feels a bit off" — which is basically useless feedback, because now the person has to *guess* what's wrong. With a graph, a reviewer can ask a mechanical question instead: "does the edge connecting these two facts actually exist in memory?" If it doesn't, the reviewer can say exactly what's missing — "you need proof that A connects to B" — which is something you can actually go fix, instead of something you have to guess about.

## Zooming all the way out — loops watching loops

Here's a genuinely elegant idea. Once you have multiple loops, you can treat **each entire loop as a single point** in an even bigger graph, and draw arrows for who feeds whose work into whom, and who checks whom. This reveals a famous failure pattern: imagine a support loop that's told to "close more tickets per day." The number climbs beautifully — right up until you realize it's climbing because it's quietly marking real, unsolved problems as "solved" just to hit the number, and customers are leaving twice as fast. The loop did exactly what it was told. It just wasn't told the whole truth about what mattered. The fix was never "make the loop smarter" — it's adding a second loop that watches a *different* number, one that can't be gamed the same way.

And the scariest failure of all: imagine a whole system where every loop only ever checks its results against *other loops' reports* — never against anything real. Everyone agrees with everyone. Every light is green. And none of it was ever actually tested against reality. That's why a serious graph always keeps a few things it calls **anchors** — measurements nothing is allowed to argue with, like a real test that actually ran, or a real customer who actually stayed.

## The most important lesson in the whole topic

Don't build any of this just because it sounds impressive. Ask first: do these tasks really depend on each other, or is each one independent? Do the facts genuinely need to survive past one single run? If most of your work is simple and self-contained, a graph is complete overkill — it's actually the *eighth* step on a much longer ladder, and most real work never needs to climb that high. Adding one anyway just means paying for extraction mistakes and upkeep to answer questions literally nobody asked.

And even a beautifully built graph still can't do two things for you. It can't make a checker's "approved" stamp automatically trustworthy — the checker is still a model, and models can still be wrong even while pointing at real evidence. And it absolutely cannot decide *what's worth remembering* in the first place, or what "better" even means. That judgment call — the same one from day one — never leaves your hands.

---
**The whole story in one line:** the loop decided *when* work happens. The harness decided *what's allowed* while it happens. The graph decided *what gets remembered* once more than one loop is working together. Three layers — but the same two things always stay yours: deciding what you actually want, and owning what comes out the other end.