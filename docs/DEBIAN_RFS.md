# Debian RFS for network-monitor

The source package `network-monitor 1.0.9-3` was accepted by
<https://mentors.debian.net> on 2026-11-08 02:07 UTC.

- Package page: <https://mentors.debian.net/package/network-monitor/>
- Source package:
  <https://mentors.debian.net/debian/pool/main/n/network-monitor/network-monitor_1.0.9-3.dsc>
- Uploader: `asem shahen <asemshahen5@gmail.com>`
- Distribution: `unstable`
- Sponsor status: **needs a sponsor**

The package is not in the Debian archive yet. The next step is a Request for
Sponsorship (RFS) bug against the `sponsorship-requests` pseudo-package.

## Send the RFS email

Send this message from `asemshahen5@gmail.com` to
`submit@bugs.debian.org`. The `[ITP]` marker is required because this is a new
package.

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

1. Wait for the BTS acknowledgement with the bug number.
2. Subscribe to the `debian-mentors` mailing list and to the RFS bug.
3. Reply to reviewer comments on the bug with a new source upload when needed.
4. Do not close the RFS bug in `debian/changelog`; the sponsor closes it after
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

الحزمة ليست في أرشيف Debian بعد. الخطوة التالية هي إرسال خطأ RFS إلى
`sponsorship-requests`.

## إرسال البريد

أرسل القالب الإنجليزي أعلاه من `asemshahen5@gmail.com` إلى
`submit@bugs.debian.org`، مع إبقاء `[ITP]` في عنوان الرسالة لأنه حزمة جديدة.
لا ترسل الرسالة من عنوان آخر؛ يجب أن يطابق عنوان المرسل عنوان صاحب الحزمة.

## بعد الإرسال

1. انتظر رسالة الإقرار التي تحتوي رقم خطأ BTS.
2. اشترك في قائمة `debian-mentors` وفي خطأ RFS.
3. ردّ على ملاحظات المراجع في الخطأ، وارفع نسخة مصدر جديدة عند الطلب.
4. لا تغلق خطأ RFS في `debian/changelog`؛ الراعي هو من يغلقه بعد الرفع إلى
   أرشيف Debian.
