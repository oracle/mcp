package com.oracle.database.jdbc.oauth;

import java.util.UUID;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * The TokenGenerator class is a singleton utility for generating and verifying a unique authorization token.
 * It uses a randomly generated UUID as the token, which is created once during class initialization.
 * This class provides methods to retrieve the singleton instance and to verify if a given token matches the generated one.
 * <p>
 * Note: This implementation generates the token only once per JVM session and logs it at the INFO level.
 * </p>
 */
public class TokenGenerator {
  private static final Logger LOG = Logger.getLogger(TokenGenerator.class.getName());
  private static final TokenGenerator INSTANCE = new TokenGenerator();

  private final String generatedToken;

  private TokenGenerator() {
    generatedToken = UUID.randomUUID().toString();
    LOG.log(Level.INFO, "Authorization token generated: {0}", generatedToken);
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
