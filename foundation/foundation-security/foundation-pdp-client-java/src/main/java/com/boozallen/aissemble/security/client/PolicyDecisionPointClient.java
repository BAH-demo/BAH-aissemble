package com.boozallen.aissemble.security.client;

/*-
 * #%L
 * AIOps Foundation::AIOps Core Security::AIOps Policy Decision Point Client
 * %%
 * Copyright (C) 2021 Booz Allen
 * %%
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *      http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * #L%
 */

import com.boozallen.aissemble.security.authorization.models.AuthRequest;
import com.boozallen.aissemble.security.authorization.models.PDPRequest;
import com.boozallen.aissemble.security.authorization.policy.PolicyDecision;
import com.boozallen.aissemble.security.config.SecurityConfiguration;
import org.aeonbits.owner.KrauseningConfigFactory;
import org.jboss.resteasy.client.jaxrs.ResteasyClient;
import org.jboss.resteasy.client.jaxrs.ResteasyWebTarget;
import org.jboss.resteasy.client.jaxrs.internal.ResteasyClientBuilderImpl;

public class PolicyDecisionPointClient {
    private final SecurityConfiguration config = KrauseningConfigFactory.create(SecurityConfiguration.class);

    public PolicyDecisionPointClient() {
    }

    public String getPolicyDecision(PDPRequest request) {
        String decision = "";
        //If authentication is disabled we should permit
        if(config.authenticationEnabled()){
            ResteasyClient client = new ResteasyClientBuilderImpl().build();
            ResteasyWebTarget target = client.target(config.getPdpHost());
            PolicyDecisionPointProxy simpleClient = target.proxy(PolicyDecisionPointProxy.class);
            decision = simpleClient.getDecision(request);
        } else {
            decision = PolicyDecision.PERMIT.toString();
        }

        return decision;
    }

    public String authenticate(AuthRequest authRequest) {
        String jwt = "";
        if(config.authenticationEnabled()) {
            ResteasyClient client = new ResteasyClientBuilderImpl().build();
            ResteasyWebTarget target = client.target(config.getPdpHost());
            PolicyDecisionPointProxy simpleClient = target.proxy(PolicyDecisionPointProxy.class);
            jwt = simpleClient.authenticate(authRequest);
        } else {
            jwt = config.getGenericJWTToken();
        }

        return jwt;
    }
}
