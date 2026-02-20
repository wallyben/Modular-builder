from __future__ import annotations

from .schemas import OutreachDraft, Prospect

_VALUE_NOTE_THRESHOLD = 500_000  # EUR — mention value if above this


def _value_note(prospect: Prospect) -> str:
    if prospect.value_eur and prospect.value_eur >= _VALUE_NOTE_THRESHOLD:
        m = prospect.value_eur / 1_000_000
        return f"We noted the contract was valued at approximately €{m:.1f}m. "
    return ""


def draft_outreach(prospect: Prospect) -> OutreachDraft:
    name = prospect.company_name
    authority = prospect.authority or "the contracting authority"
    contract = prospect.contract_title or "the facilities management contract"
    value_note = _value_note(prospect)

    subject = f"Helping {name} win more public contracts — compliance mapping"

    email_1 = (
        f"Hi [First Name],\n\n"
        f"I came across {name}'s recent award for {contract} with {authority}. "
        f"{value_note}"
        f"Congratulations — that's a strong win.\n\n"
        f"We work with FM contractors to close the compliance and evidence gaps that "
        f"cost points on rated criteria — methodology, environmental plans, key personnel CVs, "
        f"and local participation statements.\n\n"
        f"Most teams lose 15–30 % of available points not because of capability, but because "
        f"the evidence isn't structured the way evaluators expect.\n\n"
        f"Would a 20-minute call be useful to walk through where {name} typically scores "
        f"versus where the points are available?\n\n"
        f"Best,\n[Your Name]\n[Your Company]"
    )

    followup_1 = (
        f"Hi [First Name],\n\n"
        f"Just following up on my note last week about compliance mapping for {name}.\n\n"
        f"We've recently helped similar FM contractors lift their scored-criteria results "
        f"by building reusable evidence packs — ISO certs indexed to evaluation criteria, "
        f"risk registers pre-mapped to tender questions, and methodology templates "
        f"that survive re-use across different authorities.\n\n"
        f"Happy to share a short example if it would be useful. Worth a quick call?\n\n"
        f"Best,\n[Your Name]"
    )

    followup_2 = (
        f"Hi [First Name],\n\n"
        f"Last nudge from me on this.\n\n"
        f"If now isn't the right time, I'm happy to reconnect when {name} has a live "
        f"tender pipeline. We typically engage 4–8 weeks before a submission deadline.\n\n"
        f"Either way, best of luck with upcoming bids.\n\n"
        f"Best,\n[Your Name]"
    )

    loom_script = (
        f"[OPEN ON SCREEN: Award notice for {contract}]\n\n"
        f"Hey {name} team — quick two-minute walkthrough.\n\n"
        f"You recently won {contract} with {authority}. Great result. "
        f"What I want to show you is how the compliance matrix for a typical FM tender "
        f"breaks down, and where the evidence gaps usually sit.\n\n"
        f"[SWITCH TO: compliance matrix template]\n\n"
        f"These rated criteria — methodology, environment plan, key personnel — "
        f"are where most FM contractors leave points on the table. Not because they "
        f"lack the capability, but because the evidence isn't mapped to the question.\n\n"
        f"We build that mapping for you, so the next submission lands with evaluators "
        f"already seeing exactly the evidence they need.\n\n"
        f"If this looks useful, book a 20-minute call using the link below. No pitch — "
        f"just a look at your current bid documents and where we can tighten things up.\n\n"
        f"[END]"
    )

    return OutreachDraft(
        company_name=name,
        subject=subject,
        email_1=email_1,
        followup_1=followup_1,
        followup_2=followup_2,
        loom_script=loom_script,
    )
