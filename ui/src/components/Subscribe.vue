<template>
  <v-container>
    <v-layout wrap>
      <v-flex sm12 md6 offset-md3>
        <v-card elevation="4" light tag="section">
          <v-card-title>
            <v-layout align-center justify-space-between>
              <h3 class="headline">
                Subscribe
              </h3>
              <v-flex>
                <v-img :alt="theme.name" class="ml-3" contain height="48px" position="center right" :src="theme.logo"></v-img>
              </v-flex>
            </v-layout>
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <p>Subscribe with your email and password:</p>
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
              <v-layout
                row
                wrap
                class="mt-6"
              >
                <v-flex xs6 class="px-3">
                  <v-text-field
                    outline
                    label="Card number"
                    type="text"
                    v-model="form.cc"
                  ></v-text-field>
                </v-flex>
                <v-flex xs3 class="px-3">
                  <v-combobox
                    outline
                    label="Exp. month"
                    type="text"
                    v-model="form.expMonth"
                    :items="months"
                  ></v-combobox>
                </v-flex>
                <v-flex xs3 class="px-3">
                  <v-combobox
                    outline
                    label="Expiration year"
                    type="text"
                    v-model="form.expYear"
                    :items="years"
                  ></v-combobox>
                </v-flex>
              </v-layout>              
              <v-layout
                row
                wrap
                class="mt-6"
              >
                <v-flex xs7 class="px-3">
                  <v-text-field
                    outline
                    label="Name"
                    type="text"
                    v-model="form.name"
                  ></v-text-field>
                </v-flex>
                <v-flex xs3 class="px-3">
                  <v-text-field
                    outline
                    label="Zipcode"
                    type="text"
                    v-model="form.zip"
                  ></v-text-field>
                </v-flex>
                <v-flex xs2 class="px-3">
                  <v-text-field
                    outline
                    label="CVC"
                    type="text"
                    v-model="form.cvc"
                  ></v-text-field>
                </v-flex>
              </v-layout>              
              <v-layout
                row
                wrap
                class="mt-6"
              >
                <v-flex xs7 class="px-3">
                </v-flex>
                  <vue-simple-recaptcha/>
              </v-layout>
              <v-layout
                row
                wrap
                class="mt-6"
              >
                <v-flex xs7 class="px-3">
                </v-flex>
                  <stripe-element-card/>
              </v-layout>
            </v-form>
          </v-card-text>
          <v-divider></v-divider>
          <v-card-actions :class="{ 'pa-3': $vuetify.breakpoint.smAndUp }">
            <v-btn color="info" flat>
              Forgot password?
            </v-btn>
            <v-spacer></v-spacer>
            <v-btn
              @click="onSubscribe"
              color="success"
              large
            >
              <v-icon left>card_membership</v-icon>
              Subscribe
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
import { StripeElementCard } from '@vue-stripe/vue-stripe';
import VueSimpleRecaptcha from "vue-simple-recaptcha";

export default {
  name: 'Subscribe',

  components: {
    StripeElementCard,
    VueSimpleRecaptcha,
  },

  data() {
    let year = (new Date()).getFullYear();
    const years = [];

    for (let i = 0; i < 10; i++) {
      years.push(year + i);
    }

    return {
      theme: window.CesiumTheme,
      months: [
        'January', 'February', 'March', 'April', 'May', 'June', 'July',
        'August', 'September', 'October', 'November', 'December',
      ],
      years,
      form: {
        email: null,
        password: null,
        cc: null,
        expMonth: null,
        expYear: null,
        zip: null,
        cvc: null,
      },
    };
  },

  methods: {
    onSubscribe() {
      // TODO: submit form.
    },
  },
}
</script>

<style scoped>

</style>
