import { useId, useState, type FormEvent } from "react";
import { AnimatePresence, motion } from "motion/react";
import { school, whatsappLink } from "../data/site";
import { MaskLines, Reveal, SectionLabel } from "./ui/primitives";
import { ArrowRight, Check, Phone, WhatsApp } from "./ui/Icons";

const classes = [
  "Play Group",
  "Nursery",
  "Prep",
  "Class 1",
  "Class 2",
  "Class 3",
  "Class 4",
  "Class 5",
  "Class 6",
  "Class 7",
  "Class 8",
  "Pre-Nine",
];

type Errors = Partial<Record<"parent" | "phone" | "grade", string>>;

export function Admissions() {
  return (
    <section
      id="admissions"
      data-nav-dark
      aria-labelledby="admissions-title"
      className="grain relative overflow-hidden bg-ink py-24 text-chalk sm:py-32"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute -right-40 -top-40 size-[34rem] rounded-full bg-royal/60 blur-[120px]"
      />
      <div className="container-x relative grid gap-14 lg:grid-cols-12 lg:gap-10">
        <div className="lg:col-span-5">
          <SectionLabel n="05" tone="light">
            Admissions
          </SectionLabel>
          <h2 id="admissions-title" className="heading mt-5 text-[clamp(2.8rem,6.4vw,5.8rem)]">
            <MaskLines lines={["Admissions", <span key="o" className="text-sun">open.</span>]} />
          </h2>
          <Reveal delay={0.15}>
            <p className="mt-6 max-w-md text-[1.1rem] text-white/75">
              Session {school.session} is now enrolling from <strong className="text-white">{school.admissionClasses}</strong>.
              Tell us a little about your child and the form opens WhatsApp with your message ready to send.
            </p>
            <ul className="mt-10 grid max-w-md gap-px overflow-hidden rounded-2xl bg-white/10">
              {school.phones.map((p, i) => (
                <li key={p.href}>
                  <a
                    href={p.href}
                    className="group flex items-center justify-between bg-ink px-5 py-4 transition-colors hover:bg-ink-2"
                  >
                    <span>
                      <span className="block text-xs uppercase tracking-[0.14em] text-white/50">
                        {i === 2 ? "Mobile" : "School office"}
                      </span>
                      <span className="mt-0.5 block text-lg font-semibold tabular-nums">{p.label}</span>
                    </span>
                    <span className="grid size-10 place-items-center rounded-full bg-white/10 text-sun transition-colors group-hover:bg-sun group-hover:text-ink">
                      <Phone size={18} />
                    </span>
                  </a>
                </li>
              ))}
            </ul>
          </Reveal>
        </div>

        <div className="lg:col-span-6 lg:col-start-7">
          <Reveal y={40}>
            <AdmissionForm />
          </Reveal>
        </div>
      </div>
    </section>
  );
}

function AdmissionForm() {
  const uid = useId();
  const [errors, setErrors] = useState<Errors>({});
  const [sent, setSent] = useState(false);

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    const parent = String(data.get("parent") ?? "").trim();
    const phone = String(data.get("phone") ?? "").trim();
    const child = String(data.get("child") ?? "").trim();
    const grade = String(data.get("grade") ?? "").trim();
    const message = String(data.get("message") ?? "").trim();

    const next: Errors = {};
    if (parent.length < 2) next.parent = "Please enter your name.";
    if (phone.replace(/\D/g, "").length < 10) next.phone = "Please enter a phone number we can call back.";
    if (!grade) next.grade = "Please choose a class.";
    setErrors(next);
    if (Object.keys(next).length) {
      const first = e.currentTarget.querySelector<HTMLElement>(`[name="${Object.keys(next)[0]}"]`);
      first?.focus();
      return;
    }

    const details = [
      `Parent / guardian: ${parent}`,
      `Phone: ${phone}`,
      child ? `Child's name: ${child}` : null,
      `Class: ${grade} (session ${school.session})`,
      message ? `Message: ${message}` : null,
    ].filter(Boolean);
    const text = ["Assalam o Alaikum, I'd like to apply for admission at AIMS Grammar High School.", "", ...details].join("\n");

    window.open(whatsappLink(text), "_blank", "noopener,noreferrer");
    setSent(true);
  }

  const field =
    "mt-2 block w-full rounded-xl border-0 bg-paper px-4 py-3.5 text-[1rem] text-ink ring-1 ring-inset ring-line placeholder:text-ink/40 transition-shadow focus:outline-none focus:ring-2 focus:ring-royal aria-[invalid=true]:ring-2 aria-[invalid=true]:ring-crayon";

  return (
    <div className="relative rounded-[var(--radius-card)] bg-chalk p-6 text-ink shadow-[0_40px_80px_-30px_rgb(0_0_0/0.6)] sm:p-9">
      <AnimatePresence mode="wait" initial={false}>
        {sent ? (
          <motion.div
            key="sent"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.4 }}
            className="flex min-h-[28rem] flex-col items-start justify-center"
            role="status"
          >
            <span className="grid size-14 place-items-center rounded-full bg-desk text-white">
              <Check size={28} />
            </span>
            <h3 className="heading mt-6 text-[2.2rem]">WhatsApp is open.</h3>
            <p className="mt-3 max-w-sm text-muted">
              Your message is ready. Just press send. If WhatsApp didn’t open, call us on{" "}
              <a className="font-semibold text-ink underline decoration-sun decoration-2 underline-offset-4" href={school.phones[0].href}>
                {school.phones[0].label}
              </a>
              .
            </p>
            <button
              type="button"
              onClick={() => setSent(false)}
              className="mt-8 rounded-full px-5 py-3 font-semibold ring-1 ring-inset ring-line transition-colors hover:bg-paper"
            >
              Fill in another form
            </button>
          </motion.div>
        ) : (
          <motion.form
            key="form"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            noValidate
            onSubmit={onSubmit}
            aria-describedby={`${uid}-intro`}
          >
            <h3 className="heading text-[1.9rem]">Admission enquiry</h3>
            <p id={`${uid}-intro`} className="mt-1 text-[0.95rem] text-muted">
              Takes under a minute. Fields marked * are required.
            </p>

            <div className="mt-7 grid gap-5 sm:grid-cols-2">
              <Field id={`${uid}-parent`} label="Parent / guardian name *" error={errors.parent}>
                <input
                  id={`${uid}-parent`}
                  name="parent"
                  autoComplete="name"
                  className={field}
                  aria-invalid={!!errors.parent}
                  aria-describedby={errors.parent ? `${uid}-parent-err` : undefined}
                />
              </Field>
              <Field id={`${uid}-phone`} label="Phone / WhatsApp *" error={errors.phone}>
                <input
                  id={`${uid}-phone`}
                  name="phone"
                  type="tel"
                  inputMode="tel"
                  autoComplete="tel"
                  placeholder="03xx-xxxxxxx"
                  className={field}
                  aria-invalid={!!errors.phone}
                  aria-describedby={errors.phone ? `${uid}-phone-err` : undefined}
                />
              </Field>
              <Field id={`${uid}-child`} label="Child’s name">
                <input id={`${uid}-child`} name="child" className={field} />
              </Field>
              <Field id={`${uid}-grade`} label="Class applying for *" error={errors.grade}>
                <select
                  id={`${uid}-grade`}
                  name="grade"
                  defaultValue=""
                  className={`${field} appearance-none bg-[url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%230E1838' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E")] bg-[length:14px] bg-[right_1rem_center] bg-no-repeat pr-10`}
                  aria-invalid={!!errors.grade}
                  aria-describedby={errors.grade ? `${uid}-grade-err` : undefined}
                >
                  <option value="" disabled>
                    Choose a class
                  </option>
                  {classes.map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </Field>
              <Field id={`${uid}-msg`} label="Anything we should know?" wide>
                <textarea id={`${uid}-msg`} name="message" rows={3} className={`${field} resize-none`} />
              </Field>
            </div>

            <button
              type="submit"
              className="group mt-7 flex min-h-14 w-full items-center justify-center gap-3 rounded-full bg-ink px-6 text-[1.02rem] font-semibold text-chalk transition-[background-color,transform] duration-300 hover:-translate-y-0.5 hover:bg-royal"
            >
              <WhatsApp size={20} className="text-sun" />
              Send on WhatsApp
              <ArrowRight size={18} className="transition-transform duration-300 group-hover:translate-x-1" />
            </button>
            <p className="mt-4 text-center text-[0.85rem] text-muted">
              Or call{" "}
              <a href={school.phones[0].href} className="font-semibold text-ink underline decoration-sun decoration-2 underline-offset-4">
                {school.phones[0].label}
              </a>
            </p>
          </motion.form>
        )}
      </AnimatePresence>
    </div>
  );
}

function Field({
  id,
  label,
  error,
  wide,
  children,
}: {
  id: string;
  label: string;
  error?: string;
  wide?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className={wide ? "sm:col-span-2" : undefined}>
      <label htmlFor={id} className="text-[0.9rem] font-semibold text-ink">
        {label}
      </label>
      {children}
      <AnimatePresence>
        {error && (
          <motion.p
            id={`${id}-err`}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-1.5 text-[0.85rem] font-medium text-crayon"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
}
