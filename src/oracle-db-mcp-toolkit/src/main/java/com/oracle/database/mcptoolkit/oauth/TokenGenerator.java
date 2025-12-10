package com.oracle.database.mcptoolkit.oauth;

import static com.oracle.database.mcptoolkit.LoadedConstants.ORACLE_DB_TOOLBOX_AUTH_TOKEN;

import java.util.UUID;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * The TokenGenerator class is responsible for generating and verifying authorization tokens.
 * It follows the singleton pattern to ensure a single instance throughout the application.
 * <p>
 * The generated token can be overridden using the {@code ORACLE_DB_TOOLBOX_AUTH_TOKEN} environment variable.
 * If not overridden, a random UUID is used as the token.
 */
public class TokenGenerator {
  private static final Logger LOG = Logger.getLogger(TokenGenerator.class.getName());
  private static final TokenGenerator INSTANCE = new TokenGenerator();

  private final String generatedToken;

  /**
   * Private constructor to prevent instantiation from outside the class.
   * Initializes the generated token based on the {@code ORACLE_DB_TOOLBOX_AUTH_TOKEN} environment variable or a random UUID.
   */
  private TokenGenerator() {
    generatedToken = ORACLE_DB_TOOLBOX_AUTH_TOKEN != null ? ORACLE_DB_TOOLBOX_AUTH_TOKEN : UUID.randomUUID().toString() ;
    LOG.log(Level.INFO, "Authorization token generated (for testing and development use only): {0}", generatedToken);
  }

  /**
   * Returns the singleton instance of the TokenGenerator.
   * This method ensures that only one instance of the class exists throughout the application.
   *
   * @return the singleton TokenGenerator instance
   */
  public static TokenGenerator getInstance() {
    return INSTANCE;
  }

  /**
   * Verifies if the provided token matches the internally generated token.
   * This method performs a case-sensitive string comparison.
   *
   * @param token the token to verify against the generated token
   * @return true if the provided token equals the generated token, false otherwise
   */
  public boolean verifyToken(final String token) {
    return generatedToken.equals(token);
  }

}
