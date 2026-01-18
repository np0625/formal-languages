#
# Parts of text:
# 1. Title (only one)
# 2. Header (many)
# 3. Sentence
# 4. Inter-word break
# 5. Paragraph
# 6. Inter-paragraph break
# 7. Section
# 8. Inter-section break
# 9. Word
# 9.1 Identifier (a reference or a gene name)
# 10. Sentence ender (periods)
# 11. Other punctuation (commas, semicolons, dashes, colons, ...)
# 12. "Whole Text"

s = """All of the graph‐based reasoning converges on a single candidate—Betamethasone—as a putative therapy for Leber hereditary optic neuropathy (LHON).  The chains fall into three thematic clusters:

“Interaction → p53” paths
• Betamethasone is said to “interact with” a panel of unrelated small molecules (dactinomycin, fenofibrate, selumetinib, etc.).
• Each partner molecule has literature linking it to modulation of TP53.
• A Japanese case–control study (PMID 15838728) shows that a TP53 Arg72 polymorphism modifies age of LHON onset, providing a legitimate TP53–LHON association.

Weaknesses:
– No evidence is offered that Betamethasone itself alters TP53; the graph relies on an “interacts-with” edge that is typically derived from co-administration records or in-vitro binding screens, not a causal pharmacodynamic effect.
– The TP53 polymorphism is a disease modifier, not a therapeutic target; lowering or raising p53 activity has never been shown to rescue mitochondrial complex-I dysfunction that drives LHON.

Glucocorticoid‐receptor & acetylcholinesterase paths
• Betamethasone, as a corticosteroid, binds NR3C1 (glucocorticoid receptor).  NR3C1 is loosely associated in the literature with nonspecific “neuropathy” phenotypes, which are then connected to LHON via a “neuropathy → manifestation of LHON” edge (PMID 22019873).
• Similar logic is applied to ACHE and postural tremor/movement disorder.

Weaknesses:
– These are two-hop disease–disease bridges based on very broad phenotype terms (“neuropathy”, “movement disorder”).  They do not speak to the primary retinal ganglion cell degeneration seen in LHON and offer no mechanistic rationale for corticosteroid benefit.
– No clinical or pre-clinical study indicates that Betamethasone improves visual outcome in LHON; on the contrary, steroids are routinely ineffective in mitochondrial optic neuropathies that are initially misdiagnosed as optic neuritis.

IL-1 cytokine paths
• Betamethasone “interacts with” rilonacept or infliximab; those biologics modulate IL-1A/IL-1B, and IL-1 genes are asserted to be “associated with LHON” on the basis of PMID 7979221.
• PMID 7979221 is, in reality, a 1994 immunohistochemical study of cytokines in HIV myopathy; it does not mention LHON, making this edge spurious.

Overall assessment

• Evidence quality: extremely low.  Nearly all links are indirect, multi-hop, and hinge on generic interaction edges or on phenotypes only tangentially related to LHON.  The single solid paper (PMID 15838728) implicates TP53 as a modifier gene but provides no therapeutic angle for Betamethasone.

• Plausibility: poor.  Betamethasone’s known pharmacology (glucocorticoid receptor agonism) does not address the mitochondrial complex-I dysfunction or reactive oxygen species overproduction that underlie LHON, and there is no animal or human evidence of efficacy.

• Clinical readiness: none.  No registered trials, case series, or even anecdotal reports support corticosteroid use in LHON, and prior clinical experience generally shows no visual gain from steroids in these patients.

In short, the graph offers speculative, computation-driven connections that do not translate into a credible therapeutic hypothesis.  Current practice should continue to focus on agents with direct mitochondrial mechanisms (e.g., idebenone, EPI-743) until substantive experimental data emerge for corticosteroids."""

#for char in s:
#    print(f"-{char}-")


#
# Basic Kleene-style REs:
# - alphabet: keep it simple, [a-z0-9]. No escapes, so the operator symbols are not part of the alphabet
# - Operators:
#   - '*', '|', '(', ')'
# - We are leaving out '.', '?', and '+' for now, as these are all expressible as
#   more basic constructs:
#   - '.': (a|b|c|...entire alphabet...) # Wow, that's inconvenient
#   - '?': (a|ε)
#   - '+': (aa*)
#
# So we need to write a grammar for these KREs, let's call them:
# KRE ::= ε
#      | a | b | ... z | 0 | 1 ... 9
#      | KRE KRE
#      | KRE "|" KRE
#      | "(" KRE ")"
#      | KRE "*"
#
# We also need a data structure for storing a parsed RE.
# "re string" -> RE IR -> NFA


def matcher_aux(s, re, s_idx, re_idx, s_len, re_len):
    done = False
    while not done:
        if re_idx == re_len: # later add s_idx == s_len
            break
        # cur_char = s[s_idx]
        cur_regex = re[re_idx]
        cur_regex_type = cur_regex[0]
        cur_regex_expr = cur_regex[1]
        match cur_regex_type:
            case 'literal':
                print(f"a literal: {cur_regex}")
                s_idx += 1
                re_idx += 1
            case 'union':
                print(f"the union for ever: {cur_regex_expr}")
                for r in cur_regex_expr:
                    print(r)
                    # updates s_idx globally, uses local re_idx
                    matcher_aux(s, (r, ), s_idx, 0, s_len, 1)
                re_idx += 1
            case 'star':
                print(f"the big star: {cur_regex_expr}")                
                matcher_aux(s, cur_regex_expr, s_idx, 0, s_len, len(cur_regex_expr))
                re_idx += 1
            case _:
                print(f"HOW COULD THIS HAPPEN?? {cur_regex_type}")
                break
    print("done")

def matcher(s, re):
    matcher_aux(s, re, 0, 0, len(s), len(re))

print("start")
# re = "a(d|e)"
re = (('literal', 'a'), ('union', (('literal', 'd'), ('literal', 'e'))))
s1 = "ad"
s2 = "ae"

s_idx = 0
re_idx = 0
s_len = len(s)
re_len = len(re)
done = False
match_record = {}

# re2 = f(qp)*
re2 = (('literal', 'f'), ('star', (('literal', 'q'), ('literal', 'p'))))
# re3 = (ab)*(p|q)(x|y)*z
re3 = (('star', (('literal', 'a'), ('literal', 'b'))),
       ('union', (('literal', 'p'), ('literal', 'q'))),
       ('star', (('union',
                     (('literal', 'x'), ('literal', 'y'))), )),
       ('literal', 'z')
       )
# re4 = (x|y)*z
re4 = (('star', (('union',
                     (('literal', 'x'), ('literal', 'y'))), )),
       ('literal', 'z')
       )
# re5 = (ab)*
re5 = (('star', (('literal', 'a'), ('literal', 'b'))), )
# re6 = (a|b)
re6 = (('union', (('literal', 'a'), ('literal', 'b'))), )

matcher('', re3)

print("end")
