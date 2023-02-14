import { NgModule } from "@angular/core";
import { RouterModule, Routes } from "@angular/router";
import { LandingComponent } from "./landing/landing.component";
import { DetailsComponent } from "./user/details/details.component";
import { GroupsComponent } from "./user/groups/groups.component";
import { PlaylistsComponent } from "./user/playlists/playlists.component";
import { UserComponent } from "./user/user.component";

const appRoutes: Routes = [
  { path: '', component: LandingComponent, pathMatch: 'full' },
  { path: 'user', component: UserComponent,
    children: [
      { path: 'playlists', component: PlaylistsComponent },
      { path: 'groups', component: GroupsComponent },
      { path: 'details', component: DetailsComponent }
    ]},
  { path: '**', redirectTo: 'landing' }
]

@NgModule({
  imports: [RouterModule.forRoot(appRoutes)],
  exports: [RouterModule]
})
export class AppRoutingModule {
}
