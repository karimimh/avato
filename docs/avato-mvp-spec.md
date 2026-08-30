# Persian Voice-Note-to-Reel Maker — MVP Product Specification

**Document status:** MVP definition  
**Market:** Iranian consumers  
**Document date:** 30 August 2026  
**Scope:** Product concept, user experience, business model, and launch requirements only. This document intentionally excludes software architecture, technology choices, infrastructure, models, APIs, and implementation instructions.

---

## 1. Product Summary

The product turns a short Persian voice note and a small collection of personal photos or video clips into a polished vertical video that is ready to share as an Instagram Reel, Story, short video, or status.

The user should not need video-editing knowledge. They provide:

1. A recorded or uploaded Persian voice note.
2. One or more photos or short video clips.
3. A visual style.
4. An optional title and background-music choice.

The product automatically produces:

- Cleaned and volume-balanced narration.
- Editable Persian subtitles synchronized with the speech.
- Automatic visual timing based on phrases and pauses.
- Simple motion and transitions.
- Optional background music mixed below the narration.
- A title and cover frame.
- A finished vertical video.

### Core promise

> **Record a voice note, choose your photos, and receive a ready-to-share Persian Reel.**

### Suggested Persian positioning

> **ویس و عکس‌هات رو بده؛ ریلز آماده تحویل بگیر.**

---

## 2. Market Finding and Opportunity

A search of Iranian consumer apps, Persian websites, Café Bazaar, Myket, and Iranian iOS distribution channels found several adjacent products, but no clearly established Iranian product dedicated to the complete workflow:

> **Persian voice note + personal photos or clips → automatically timed, subtitled, ready-to-share vertical Reel**

The closest local products currently cover separate parts of the workflow:

| Product | What it currently covers | Important gap compared with this product |
|---|---|---|
| Capzy | Automatic Persian subtitles and turning long videos or podcasts into short clips | Primarily starts with an existing video or long-form recording; it is not centered on combining a casual voice note with the user's personal photos |
| Capzo | Audio transcription, SRT generation, captioned video, and intelligent Reel cutting for editors | More editing-oriented; it does not present a one-step consumer flow that sequences personal photos around a voice note |
| Hodhod | Persian speech-to-text, subtitles, translation, and text-to-speech | Produces text or subtitle assets rather than a finished photo-and-voice Reel |
| Viditor | Template-based online video creation with uploaded photos, video, music, and narration | Requires template editing and manual content placement; it does not automatically transcribe and time a voice note around personal media |
| Persian AI Assistant | Generates a vertical Reel from a topic, generated script, narration, images, and video | Starts from a topic and generated content rather than the user's authentic voice note and personal memories |
| Generic slideshow and video editors | Combine photos, music, text, and effects | Require manual editing and generally lack a Persian-first automatic voice-note workflow |

### Conclusion

The market is **not empty**, but the exact product positioning remains differentiated. The opportunity is not to build another general video editor or subtitle generator. The opportunity is to make the shortest possible path from an ordinary person's existing behavior—sending a voice note and selecting phone-gallery media—to a polished short video.

The competitive risk is real because existing subtitle or template-video products could add similar functionality. The MVP must therefore lead with a very clear workflow, excellent Persian subtitle quality, attractive fixed templates, and simplicity rather than a large feature list.

### Research limitation

This conclusion is based on publicly discoverable products and listings as of 30 August 2026. It cannot rule out unpublished projects, private beta products, or tools promoted only inside closed social-media channels.

---

## 3. Problem Definition

Many Iranian users want to share stories, opinions, memories, educational tips, birthday messages, travel recaps, or emotional messages as short videos. However:

- They do not want to appear on camera.
- They are comfortable recording voice notes but not writing scripts.
- Their useful photos and clips are scattered in their phone gallery.
- Manual video editing is time-consuming.
- General video editors contain too many controls.
- Synchronizing Persian subtitles manually is difficult.
- Foreign services may have payment, account, language, or accessibility limitations.
- A plain voice note is less attractive and less shareable than a vertical video.

Existing tools generally make users adapt to an editing workflow. This product should adapt to the behavior users already understand: **talk, select photos, preview, share**.

---

## 4. Product Goals

The MVP must:

1. Let a new user create a usable first video without learning video editing.
2. Produce a first draft from a Persian voice note and personal media with minimal decisions.
3. Make the draft easy to correct without exposing a professional timeline editor.
4. Produce an attractive vertical video suitable for popular social platforms.
5. Support Iranian payment methods and Persian-first usage.
6. Create a visible reason to pay through better-quality, watermark-free exports.
7. encourage organic discovery when free users share watermarked videos.

---

## 5. Non-Goals

The MVP is **not**:

- A full video editor.
- A replacement for CapCut, InShot, Premiere, or similar editors.
- A long-form podcast editor.
- A text-to-video generator.
- A stock-footage generator.
- An AI-avatar product.
- A voice-cloning product.
- A social-media scheduler.
- A public social network.
- A brand-management platform.
- A business collaboration tool.
- A tool for generating fictional speech in another person's voice.

These exclusions are essential to keep the product fast to understand and limited enough to launch.

---

## 6. Target Users

### Primary audience

Persian-speaking consumers who use Instagram, Telegram, WhatsApp, Bale, Eitaa, Rubika, Aparat, or similar platforms and want attractive short videos without editing skills.

### Primary user profiles

#### A. Casual storyteller

Wants to share an opinion, short story, joke, experience, or personal thought using their own voice without appearing on camera.

#### B. Memory sharer

Wants to combine family, birthday, relationship, travel, graduation, or childhood photos with a spoken message.

#### C. Student or informal educator

Wants to explain one short concept, study tip, book idea, or useful fact over supporting images.

#### D. Small personal creator

Posts regularly but does not consider themselves a professional editor. Values speed more than detailed control.

### Users who are not the MVP priority

- Professional video editors.
- Marketing agencies.
- Large commercial content teams.
- Users needing frame-level editing.
- Users producing videos longer than one minute.
- Users whose main need is AI-generated actors or stock footage.

Businesses may still use the service, but the product language and workflow should remain consumer-oriented.

---

## 7. Main Use Cases

The MVP should serve these high-frequency or emotionally strong use cases:

1. **Personal opinion Reel**  
   A user records a 30-second opinion and adds several related images.

2. **Birthday or anniversary message**  
   A user records a heartfelt message and adds photos of the recipient.

3. **Travel recap**  
   A user narrates what happened during a trip and adds travel photos and clips.

4. **Family memory**  
   A user tells the story behind several old photographs.

5. **Educational tip**  
   A user explains one concept while showing screenshots, diagrams, book pages, or relevant photos.

6. **Short story or joke**  
   A user narrates a story while the product changes visuals and highlights subtitles.

7. **Product or purchase experience**  
   An ordinary user describes a personal experience and shows their own photos. This is not positioned as a business-advertising workflow.

8. **Faceless daily content**  
   A user who does not want to appear on camera turns regular voice notes into visual posts.

---

## 8. MVP Input Rules

A project contains the following inputs.

### 8.1 Voice note

The user can:

- Record a new voice note inside the product.
- Upload an existing audio file.
- Replace the voice note before final export.
- Listen to the original and cleaned versions.
- Trim only the beginning and end.

MVP limits:

- One voice note per project.
- Persian is the primary supported language.
- Minimum useful duration: approximately 5 seconds.
- Maximum final narration duration: 60 seconds.
- If the recording is longer than the selected format, the user must trim or choose a longer format.
- The product may remove leading silence, trailing silence, and unusually long silent gaps.
- The product must not rearrange spoken sentences or change the meaning of the narration.

### 8.2 Photos and clips

The user can select:

- Photos.
- Short video clips.
- A mixture of both.

MVP limits:

- Minimum: 1 media item.
- Recommended: 3 to 10 media items.
- Maximum: 12 media items.
- Uploaded video clips are used primarily as silent visuals under the narration.
- The original sound of uploaded clips is muted in the MVP.
- The user can reorder media before and after the first draft.
- The user can remove or replace individual media items.

### 8.3 Title

The user can optionally add:

- A short video title.
- A short secondary line.

The title appears at the start and can also be used on the cover frame. The product must work even when the user provides no title.

### 8.4 Background music

The user can choose:

- No music.
- One item from a small curated library of licensed tracks.

The MVP should offer only a small number of clearly different moods, such as:

- Calm.
- Emotional.
- Upbeat.

The user can choose between a small number of music-volume levels. Narration must always remain clear.

User-uploaded music is outside the MVP to reduce copyright confusion and unnecessary controls.

---

## 9. Output Formats

The MVP produces vertical videos only.

### Supported project lengths

- **Quick:** up to 15 seconds.
- **Standard:** up to 30 seconds.
- **Full:** up to 60 seconds.

The output length follows the cleaned narration and does not need to be exactly 15, 30, or 60 seconds.

### Output characteristics

Every completed output must include:

- Vertical 9:16 framing.
- The user's narration.
- Synchronized Persian subtitles.
- The selected photos and clips.
- Motion or transitions appropriate to the chosen template.
- Optional music.
- An optional opening title.
- A cover frame.
- A standard shareable video file.

The MVP does not need square, horizontal, or platform-specific variations.

---

## 10. Core User Journey

### Step 1: Start a project

The user chooses **Create a Reel** and sees a simple explanation:

> Record or upload a voice note, choose your photos, and we will prepare the video.

The product should not begin with a complex template browser.

### Step 2: Add the voice note

The user records or uploads audio.

Afterward, the product:

- Displays the duration.
- Detects excessive silence or poor volume.
- Offers a cleaned version.
- Warns when the audio is too long or too unclear.
- Lets the user trim the start and end.

### Step 3: Review the transcript

The product generates a Persian transcript divided into short subtitle segments.

The user can:

- Play the audio from each segment.
- Correct words.
- Merge or split subtitle segments within simple limits.
- See uncertain words highlighted.
- Restore the original transcript if needed.

The transcript is never silently rewritten as a different message.

### Step 4: Add photos and clips

The user selects up to 12 media items and can reorder them.

The product shows a simple recommendation based on narration length, for example:

> For a 30-second voice note, 5–8 photos usually works well.

### Step 5: Choose a visual style

The user selects one of three fixed templates. Each template includes its own subtitle style, motion, transitions, and cover treatment.

The user can preview a short sample before choosing.

### Step 6: Create the first draft

The product automatically:

- Divides the narration into visual sections.
- Assigns media items to those sections.
- Times visual changes near sentence or phrase boundaries.
- Adds subtitles.
- Applies template motion and transitions.
- Adds the selected music.
- Creates the opening title and cover.

### Step 7: Review the draft

The user watches the complete preview.

The user can make only the following changes:

- Correct subtitle text.
- Reorder photos and clips.
- Replace or remove a media item.
- Change which media item appears for a subtitle section.
- Change the template.
- Change or disable music.
- Change the title.
- Choose a different cover image.
- Trim the beginning or end of the narration.

The MVP must not show a multi-track editing timeline.

### Step 8: Export

The user chooses free or paid export according to account eligibility.

After completion, the user can:

- Download the video.
- Share it using the phone's standard share options.
- Return to the project for corrections.
- Delete the project.

If an export fails, no paid credit is consumed.

---

## 11. Automatic Draft Behavior

The automatic draft is the main product experience. It should follow predictable rules rather than attempting overly creative editing.

### 11.1 Narration cleanup

The draft should:

- Reduce obvious steady background noise when possible.
- Normalize narration volume.
- Remove leading and trailing silence.
- Shorten unusually long silent gaps.
- Preserve the speaker's natural voice and identity.
- Avoid artificial voice replacement.

### 11.2 Subtitle segmentation

Subtitles should:

- Be Persian-first and right-to-left.
- Use short, readable phrases.
- Avoid covering important faces where possible.
- Remain within safe screen margins.
- Stay synchronized with speech.
- Use Persian-friendly punctuation and line breaking.
- Allow manual corrections before paid export.

### 11.3 Media timing

The draft should:

- Change media near a natural phrase, pause, or sentence boundary.
- Give each media item enough time to be understood.
- Reuse media only when the user has supplied too few items.
- Avoid very rapid changes unless the selected template is designed for them.
- Preserve the user's selected order by default.
- Never invent photos or replace personal media with unrelated generated visuals.

### 11.4 Clip handling

For uploaded video clips:

- The relevant portion should fit the assigned narration segment.
- Clip audio is muted.
- Obvious excess at the beginning or end may be omitted automatically.
- The user can replace the clip if the result is unsuitable.
- Detailed clip trimming is outside the MVP.

### 11.5 Music handling

Music should:

- Begin and end smoothly.
- Remain clearly below the narration.
- Become slightly quieter while the user is speaking.
- Never prevent subtitle-free understanding of the narration.
- Use only tracks the service is permitted to provide.

---

## 12. The Three MVP Templates

The templates must look intentionally different while remaining flexible enough for all main use cases.

### Template 1: Clean Story

Best for opinions, explanations, and educational tips.

Characteristics:

- Full-screen photos or clips.
- Subtle zoom or movement.
- Clean subtitles near the lower portion of the screen.
- Current phrase highlighted.
- Minimal transitions.
- Optional short title at the start.

### Template 2: Dynamic Voice

Best for jokes, opinions, short stories, and energetic content.

Characteristics:

- Larger animated subtitle phrases.
- More visible word or phrase highlighting.
- Waveform or simple voice-reactive visual element.
- Faster but controlled visual changes.
- Strong opening title.
- Works acceptably even with only one or two photos.

### Template 3: Memory Film

Best for birthdays, relationships, family, travel, and nostalgia.

Characteristics:

- Softer transitions.
- Photo-focused composition.
- Subtle frame, date, or caption treatment.
- Emotional subtitle style.
- Slower visual movement.
- Cover design suited to a person's name, event, or trip.

Template customization in the MVP is limited to:

- A small selection of Persian fonts.
- A small selection of subtitle color treatments.
- Title text.
- Music choice.
- Cover image.

Users cannot create templates or move every element freely.

---

## 13. Editing Experience

The product should present editing as **correction**, not professional production.

### Required simple editing actions

- Edit subtitle text.
- Reorder media.
- Replace media.
- Assign media to another spoken section.
- Select a different template.
- Select a different music track.
- Turn music off.
- Change title.
- Choose cover.
- Trim voice-note start and end.

### Explicitly excluded editing actions

- Multi-track timeline.
- Keyframes.
- Per-frame transitions.
- Detailed animation controls.
- Color grading.
- Manual audio mixing.
- Multiple narration tracks.
- Stickers and large asset libraries.
- Custom effect creation.
- Advanced clip cropping.
- Scene-level generated imagery.
- Layer positioning.
- Masking.
- Background removal.
- Team comments and approval.

This limited editing model is a major part of the product's value.

---

## 14. Project Management

The user should have a simple recent-projects area showing:

- Project cover.
- Title or creation date.
- Duration.
- Draft, processing, ready, or failed status.
- Export status.
- Delete action.

MVP retention policy:

- Recent projects remain available for 30 days after the last activity.
- The user can download completed videos during this period.
- The user can permanently delete a project at any time.
- The product clearly explains when source files and outputs will be deleted.
- Long-term cloud archiving is not part of the MVP.

A user should be warned before an old project expires.

---

## 15. Free and Paid Product

### Recommended primary model

The primary model should be **pay-per-export through credit packs**, because many ordinary users will create videos occasionally rather than every week.

A lightweight monthly plan can serve repeat creators.

### Free experience

A new user receives:

- One complete trial project.
- Full preview.
- A lower-resolution export.
- A small, non-obstructive product watermark.
- Access to all three templates for evaluation.

The free version should be useful enough to share. A severely degraded free result would weaken organic acquisition.

### Credit packs

Credit packs provide:

- High-quality export.
- No watermark.
- Access to all MVP templates.
- Re-editing and re-exporting of the same project for a limited period without consuming another credit.
- Credits that remain valid long enough for occasional users.

Pack sizes should include:

- A small pack for one event or experiment.
- A medium pack for regular personal use.
- A larger pack for frequent creators.

Final prices should be determined through market testing and adjusted for inflation rather than fixed permanently in this specification.

### Monthly plan

A monthly plan may include:

- A monthly export allowance.
- No watermark.
- High-quality output.
- All templates and music.
- A lower effective cost per export.

The MVP should not introduce multiple complex subscription tiers.

### Credit-consumption rule

A credit is consumed only after a successful paid export. Failed processing or export must not charge the user.

---

## 16. Account and Onboarding Requirements

The user should be able to understand and begin the process before facing a long registration form.

Recommended flow:

1. Let the visitor start a project immediately.
2. Request an account before saving, exporting, or paying.
3. Explain the free trial clearly.
4. Avoid asking for professional details, company names, social handles, or content calendars.
5. Show a short privacy explanation before the first media upload.

The onboarding demonstration should show one realistic before-and-after example:

- Input: a voice note and several photos.
- Output: a complete vertical video.

The product should communicate that it uses the user's real voice rather than generating a fake narrator.

---

## 17. Privacy and Trust

Voice recordings and personal photos can be highly sensitive. Privacy must be visible in the product, not hidden only in legal text.

The MVP must provide:

- Private projects by default.
- No public profile or public gallery.
- Clear deletion controls.
- Clear storage-duration information.
- A statement that user media is used to create the requested video.
- A statement explaining whether any human reviewer can access uploaded media.
- A prohibition on selling or publicly reusing user media.
- A clear process for account and project deletion.
- Secure treatment of payment and account information.
- A reminder not to upload media without the necessary permission.

The product should never train public-facing features on a user's private voice or photos without separate, explicit consent.

---

## 18. Content and Rights Rules

Before exporting, users confirm that:

- They own the media or have permission to use it.
- They have permission to use the uploaded voice.
- Their content does not violate another person's privacy.
- They will not use the product for impersonation or deception.

The service should not support:

- Voice cloning.
- Fabricating speech in another person's voice.
- Non-consensual intimate media.
- Sexual content involving minors.
- Targeted harassment.
- Deceptive impersonation.
- Illegal copyrighted music distribution.
- Content that clearly violates applicable law.

The MVP does not need a complex creator-rights marketplace or automated copyright-dispute system.

---

## 19. Important Product States and Failure Handling

### Poor audio

When narration is too noisy or quiet:

- Explain the problem in simple Persian.
- Offer a cleaned preview.
- Recommend re-recording when improvement is insufficient.
- Do not let the user pay before hearing the result.

### Low-confidence transcript

When some words are uncertain:

- Highlight those words.
- Let the user replay the exact section.
- Ask for correction before final export.

### Too few visuals

When the user provides too few media items:

- Explain that some items may repeat.
- Recommend adding more.
- Allow continuation with the Dynamic Voice template.

### Too many visuals

When too many items are selected:

- Recommend the most suitable range.
- Ask the user to remove items rather than silently ignoring them.

### Export failure

- Keep the project editable.
- Show a retry action.
- Do not consume a credit.
- Preserve corrections already made.

### User leaves before completion

- Preserve the draft for the retention period.
- Return the user to the latest completed step.

---

## 20. Functional MVP Requirements

The MVP is complete only when all of the following user-visible capabilities exist:

1. Create a project.
2. Record or upload one Persian voice note.
3. Trim the beginning and end.
4. Listen to original and cleaned audio.
5. Generate an editable Persian transcript.
6. Highlight uncertain transcript words.
7. Upload 1–12 photos or short clips.
8. Reorder, remove, and replace media.
9. Enter an optional title.
10. Choose one of three fixed templates.
11. Choose no music or a curated music track.
12. Generate an automatic first draft.
13. Preview the complete result.
14. Correct subtitles.
15. Change media-to-section assignment.
16. Change template, music, title, and cover.
17. Export a watermarked free version when eligible.
18. Purchase credits using an Iranian payment method.
19. Export a high-quality watermark-free version after payment.
20. Download and share the completed video.
21. View recent projects.
22. Delete projects and account data.
23. Retry failed processing without losing payment or work.

Anything beyond this list requires evidence from users before entering the product roadmap.

---

## 21. MVP Acceptance Criteria

The product is ready for an initial public launch when:

- A first-time Persian-speaking user can create a video without a tutorial or human assistance.
- A valid project can be created from one voice note and one photo.
- A typical project with several photos produces a coherent first draft.
- Persian subtitles are readable, editable, and visibly synchronized.
- Each of the three templates produces a distinct result.
- The narration remains understandable with music enabled.
- The user can correct the result without using a timeline editor.
- A successful free export includes the expected watermark.
- A successful paid export removes the watermark.
- A failed export never consumes a credit.
- Users can delete their projects.
- The full path from input to first preview feels materially easier than using a general video editor.

---

## 22. Success Metrics

The MVP should track product outcomes rather than vanity registrations.

### Acquisition and activation

- Visitors who start a project.
- New users who successfully add a voice note.
- New users who reach the first complete preview.
- Time from starting a project to first preview.

### Product quality

- Percentage of projects requiring transcript correction.
- Average number of corrected words.
- Percentage of users who keep the first selected template.
- Percentage of users replacing automatically assigned media.
- Export failure rate.
- User rating of first-draft usefulness.

### Conversion

- Preview-to-free-export rate.
- Preview-to-paid-export rate.
- Free-user-to-credit-purchase rate.
- Average credits purchased.
- Subscription adoption among repeat creators.

### Retention and sharing

- Users creating a second project.
- Projects created per paying user.
- Repeat purchase rate.
- Share action after export.
- Percentage of new users arriving through a shared watermarked video or referral link.

### Recommended validation questions

After export, ask no more than two questions:

1. “How much editing did this save you?”
2. “Would you use this again for another story or event?”

---

## 23. Main Risks and Responses

### Risk 1: Users compare it with free general editors

**Response:** Compete on speed and simplicity, not editing depth. The product must generate a usable draft automatically rather than merely offer editing tools.

### Risk 2: Existing local subtitle products add similar functionality

**Response:** Own the voice-note-first consumer positioning, personal-media workflow, three recognizable templates, and emotional use cases.

### Risk 3: Persian transcription errors damage the result

**Response:** Make correction fast, highlight uncertain words, and let users hear the exact audio segment.

### Risk 4: Automatic visual timing feels random

**Response:** Preserve user media order by default, switch visuals at natural speech boundaries, and allow simple reassignment.

### Risk 5: Users create only once

**Response:** Support both event-based one-time payments and a subscription for repeat creators. Do not rely exclusively on monthly subscriptions.

### Risk 6: Personal media creates privacy concerns

**Response:** Keep projects private, make deletion obvious, state retention clearly, and avoid a public gallery.

### Risk 7: Music creates copyright problems

**Response:** Offer only a small licensed library and no user-uploaded music in the MVP.

### Risk 8: The first draft takes too many decisions

**Response:** Ask only for voice, media, and one template. Everything else should have a sensible default.

---

## 24. Product Differentiation

The product should consistently communicate five differences:

1. **Voice-note first**  
   The user starts by speaking naturally, not by writing a script or editing a video.

2. **Personal-media first**  
   The result is built from the user's own photos and clips, not generic stock content.

3. **Persian first**  
   Transcription, subtitle layout, fonts, punctuation, and editing are designed for Persian.

4. **No editing knowledge required**  
   The default result is already complete; editing is limited to correction.

5. **Accessible to Iranian users**  
   The product supports local payment and does not require a foreign subscription or professional software.

### Positioning to avoid

Do not describe it as:

- “A professional AI video studio.”
- “An all-in-one content platform.”
- “A complete replacement for video editors.”
- “A marketing automation suite.”

These descriptions create expectations outside the MVP.

---

## 25. Suggested Landing-Page Message

### Headline

**Turn your Persian voice note into a ready-to-share Reel.**

### Supporting line

Record or upload your voice, choose your photos, and receive a subtitled vertical video—without learning video editing.

### Persian version

**ویس فارسی و عکس‌هات رو بده؛ ریلز آماده تحویل بگیر.**

ویس را ضبط کن، عکس‌ها را انتخاب کن و بدون ادیت حرفه‌ای، ویدیوی عمودی زیرنویس‌دار بساز.

### Primary action

**Create my first Reel**

### Demonstration

The landing page should show:

- The original short voice note.
- Five selected photos.
- The finished Reel.
- A visible explanation that the first draft was created automatically.

---

## 26. Example User Scenarios

### Scenario A: Birthday message

Sara records a 25-second birthday message for her sister and selects seven shared photos. She chooses Memory Film, corrects one name in the transcript, selects emotional music, and exports a vertical video to share in Instagram and the family group.

### Scenario B: Faceless opinion

Amir records a 40-second opinion about a movie and selects the poster, two screenshots, and one personal photo. He chooses Dynamic Voice. The product highlights spoken phrases and reuses the poster as a background where no other visual is available.

### Scenario C: Study tip

Niloofar records a 20-second explanation of a study method and adds four screenshots from her notes. She chooses Clean Story, corrects two technical words, disables music, and exports the result.

### Scenario D: Travel memory

A couple records a 55-second trip recap and chooses 12 photos and clips. The product follows their media order, changes visuals at sentence boundaries, and creates a cover using the trip name.

---

## 27. Features Deferred Until After Validation

The following may be considered only after the MVP demonstrates repeat usage and payment:

- Additional aspect ratios.
- Videos longer than 60 seconds.
- Automatic social captions and hashtags.
- Direct publishing to social platforms.
- User-uploaded music.
- More templates.
- Brand kits.
- Automatic selection from the entire phone gallery.
- Multi-speaker transcription.
- Translation and bilingual subtitles.
- Automatic speech rewriting or shortening.
- Generated stock images or video.
- AI avatars.
- Voice cloning.
- Collaboration.
- Public template marketplace.
- Desktop-oriented professional editor.
- Long-term project storage.
- Batch production.
- Scheduling and analytics.

None of these are required to prove the initial product.

---

## 28. Final MVP Definition

The MVP is a focused Persian consumer service with one job:

> **Convert one short voice note and up to 12 personal photos or clips into one attractive, subtitled, vertical video.**

A successful MVP does not need hundreds of effects. It needs:

- A very short creation flow.
- Reliable Persian subtitles.
- Three strong templates.
- Sensible automatic timing.
- Clear audio.
- Simple correction.
- Local payment.
- A shareable final result.

The product wins when a user who has never edited a video can move from “I have something to say” to “I have a Reel ready to share” with minimal effort.

---

## 29. Competition Research References

These references support the market-comparison section and are not implementation recommendations.

- Capzy app listing: https://cafebazaar.ir/app/org.capzy.studio
- Capzy website: https://capzy.app/
- Capzo website: https://capzo.ir/
- Hodhod website: https://hodhod.biz/
- Viditor website: https://viditor.net/
- Persian AI Assistant listing: https://cafebazaar.ir/app/com.persianaitools.ai
- CapSync listing: https://anardoni.com/ios/app/comcapsynccapsyncapp
