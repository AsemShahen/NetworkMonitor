# Debian RFS for network-monitor

The source package `network-monitor 1.0.9-3` was accepted by
<https://mentors.debian.net> on 2026-11-08 02:07 UTC.

- Package page: <https://mentors.debian.net/package/network-monitor/>
- Source package:
  <https://mentors.debian.net/debian/pool/main/n/network-monitor/network-monitor_1.0.9-3.dsc>
- Uploader: `asem shahen <asemshahen5@gmail.com>`
- Distribution: `unstable`
- Sponsor status: **needs a sponsor**

The package is not in the Debian archive yet. The Request for Sponsorship (RFS)
was filed against the `sponsorship-requests` pseudo-package:

- RFS bug: <https://bugs.debian.org/1153391>
- Status: open, wishlist severity, waiting for a Debian sponsor.
- Reported: 2026-11-08 02:41 UTC.

## Send the RFS email

The message was sent from `asemshahen5@gmail.com` to
`submit@bugs.debian.org` on 2026-11-08 05:38 +0300 (02:38 UTC). The `[ITP]`
marker is required because this is a new package. A copy of the sent message is
in `docs/DEBIAN_RFS.eml`; the canonical template follows.

```text
From: asem shahen <asemshahen5@gmail.com>
To: submit@bugs.debian.org
Subject: RFS: network-monitor/1.0.9-3 [ITP] -- per-application network monitor with usage tracking and blocking

Package: sponsorship-requests
Severity: wishlist

Dear mentors,

I am looking for a sponsor for my package "network-monitor":

 * Package name     : network-monitor
   Version          : 1.0.9-3
   Upstream contact : Asem Shahen <asemshahen5@gmail.com>
 * URL              : https://github.com/AsemShahen/NetworkMonitor
 * License          : GPL-3+
 * Vcs              : https://github.com/AsemShahen/NetworkMonitor
   Section          : net

The source builds the following binary packages:

  network-monitor - per-application network monitor with usage tracking and blocking

To access further information about this package, please visit the following URL:

  https://mentors.debian.net/package/network-monitor/

Alternatively, you can download the package with 'dget' using this command:

  dget -x https://mentors.debian.net/debian/pool/main/n/network-monitor/network-monitor_1.0.9-3.dsc

Changes for the initial release:

 network-monitor (1.0.9-3) unstable; urgency=medium
 .
   * Order the DEP-5 copyright paragraphs so the metadata license applies to
     the AppStream file.

Regards,
--
  asem shahen
```

## After sending

1. The BTS assigned bug **#1153391**; the submitter receives replies
   automatically.
2. Reply to reviewer comments on the bug with a new source upload when needed.
3. Do not close the RFS bug in `debian/changelog`; the sponsor closes it after
   the upload to the Debian archive.

The Mentors page also exposes a prefilled `mailto:` link and an RFS template on
the package page. The package must stay at `1.0.9-3` unless a reviewer requests
changes.

---

# طلب رعاية Debian (RFS)

قُبلت حزمة المصدر `network-monitor 1.0.9-3` في
<https://mentors.debian.net> بتاريخ 2026-11-08 02:07 UTC.

- صفحة الحزمة: <https://mentors.debian.net/package/network-monitor/>
- حزمة المصدر:
  <https://mentors.debian.net/debian/pool/main/n/network-monitor/network-monitor_1.0.9-3.dsc>
- البريد: `asem shahen <asemshahen5@gmail.com>`
- التوزيعة: `unstable`
- حالة الرعاية: **تحتاج إلى راعٍ**

الحزمة ليست في أرشيف Debian بعد. أُرسل طلب الرعاية (RFS) إلى
`sponsorship-requests`:

- خطأ RFS: <https://bugs.debian.org/1153391>
- الحالة: مفتوح، بأهمية wishlist، بانتظار راعٍ من Debian.
- تاريخ الإبلاغ: 2026-11-08 02:41 UTC.

## إرسال البريد

أُرسل القالب الإنجليزي أعلاه من `asemshahen5@gmail.com` إلى
`submit@bugs.debian.org` بتاريخ 2026-11-08 05:38 +0300 (02:38 UTC)، مع إبقاء
`[ITP]` في عنوان الرسالة لأنه حزمة جديدة. توجد نسخة من الرسالة المرسلة في
`docs/DEBIAN_RFS.eml`.
لا ترسل الرسالة من عنوان آخر؛ يجب أن يطابق عنوان المرسل عنوان صاحب الحزمة.

## بعد الإرسال

1. أنشأ BTS الخطأ رقم **1153391**، ويصل صاحب البلاغ الردود تلقائيًا.
2. ردّ على ملاحظات المراجع في الخطأ، وارفع نسخة مصدر جديدة عند الطلب.
3. لا تغلق خطأ RFS في `debian/changelog`؛ الراعي هو من يغلقه بعد الرفع إلى
   أرشيف Debian.
