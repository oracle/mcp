package com.oracle.database.jdbc.web;

import com.oracle.database.jdbc.oauth.OAuth2Configuration;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;

public class RedirectOAuthToOpenIDServlet extends HttpServlet {

  @Override
  protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
    final String redirectLink = OAuth2Configuration.getInstance().getAuthServer() +
      "/.well-known/openid-configuration";

    response.addHeader("Access-Control-Allow-Origin", WebUtils.getAllowedHosts());
    response.sendRedirect(redirectLink);
  }
}
