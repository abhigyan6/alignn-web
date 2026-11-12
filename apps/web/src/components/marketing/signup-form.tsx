/**
 * Early-access sign-up. Alignn has no email-capture endpoint yet, so this form
 * is rendered visibly disabled and cannot submit or send data anywhere. Replace
 * it with a FastAPI-backed form (not a client-only stub) when sign-up opens.
 */
export function SignupForm() {
  return (
    <form aria-describedby="join-status" className="lp-form">
      <fieldset disabled className="lp-form-fields">
        <legend className="lp-sr">Early-access sign-up (not open yet)</legend>
        <label className="lp-sr" htmlFor="join-email">
          Email address
        </label>
        <input
          autoComplete="email"
          id="join-email"
          name="email"
          placeholder="Email sign-up opens soon"
          type="email"
        />
        <button type="submit">Join early access</button>
      </fieldset>
      <p className="lp-form-status" id="join-status">
        This form is a placeholder and is not connected yet. We are not
        collecting email addresses.
      </p>
    </form>
  );
}
