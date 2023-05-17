<template>
  <v-container>
    <v-layout wrap>
      <v-flex sm12 md6 offset-md3>
        <v-card elevation="4" light tag="section">
          <v-card-title>
            <v-layout align-center justify-space-between>
              <h3 class="headline">
                Login
              </h3>
              <v-flex>
                <v-img :alt="theme.name" class="ml-3" contain height="48px" position="center right" :src="theme.logo"></v-img>
              </v-flex>
            </v-layout>
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <p>Login with your email and password:</p>
            <v-form>
              <v-layout row wrap class="mt-6">
                <v-flex xs12 class="px-3">
                  <v-text-field
                    outline
                    label="Email"
                    type="text"
                    v-model="form.email"
                  ></v-text-field>
                </v-flex>
              </v-layout>
              <v-layout row wrap class="mt-6 pb-6">
                <v-flex xs12 class="px-3">
                  <v-text-field
                    outline
                    hide-details
                    label="Password"
                    type="password"
                    v-model="form.password"
                  ></v-text-field>
                </v-flex>
              </v-layout>
              <v-layout row wrap class="mt-6 pb-6">
                <v-flex xs12 class="px-3">
                  <vue-simple-recaptcha
                    :sitekey="recaptchaApiKey"
                  />
                </v-flex>
              </v-layout>
            </v-form>
          </v-card-text>
          <v-divider></v-divider>
          <v-card-actions :class="{ 'pa-3': $vuetify.breakpoint.smAndUp }">
            <v-btn color="info" text>
              Forgot password?
            </v-btn>
            <v-spacer></v-spacer>
            <v-btn
              @click="onLogin"
              color="info" large
            >
              <v-icon left>lock</v-icon>
              Login
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-flex>
      <v-flex sm12 md6 offset-md3>
        <v-layout align-center justify-space-between>
          <p class="caption my-3">
            <a href="#">Privacy Policy</a>
            |
            <a href="#">Terms of Service</a>
          </p>
        </v-layout>
      </v-flex>
    </v-layout>
  </v-container>
</template>

<script>
import VueSimpleRecaptcha from "vue-simple-recaptcha";
import { RECAPTCHA_API_KEY } from "@/config";

export default {
  name: 'Login',

  components: {
    VueSimpleRecaptcha,
  },

  data() {
    return {
      theme: window.CesiumTheme,
      recaptchaApiKey: RECAPTCHA_API_KEY,
      form: {
        email: null,
        password: null,
      },
    };
  },

  methods: {
    onLogin() {
      // TODO: submit form.
    },
  },
}
</script>

<style scoped>

</style>
